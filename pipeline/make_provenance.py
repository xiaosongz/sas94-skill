"""Generate `docs/rule-provenance.md` — an audit trail mapping every Rule,
Idiom, and Hygiene entry in `references/*.md` to its upstream source URL.

Usage:

    uv --directory pipeline run python make_provenance.py > docs/rule-provenance.md

The script scans each reference file for `### Rule <N>:`, `### Idiom:`,
and `### Hygiene <N>:` headings, extracts the `Source:` URL on the
next 5 lines, and emits a sorted markdown table to stdout.

Re-running the script must produce byte-identical output — no timestamps,
everything sorted deterministically.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

from _common import REFERENCES_DIR, body_after_frontmatter, load_frontmatter

# A `### Rule N: Title...`, `### Idiom: Title...`, or `### Hygiene N: Title...`
# heading. Rule / Hygiene numbers are captured; Idioms have no number (slot
# stays empty for sorting). `Hygiene` rows are file-hygiene items demoted
# out of the Rules cap but still tracked for provenance (see data-step.md).
HEADING_RE = re.compile(r"^###\s+(Rule|Idiom|Hygiene)(?:\s+(\d+))?:\s*(.+?)\s*$")

# A `## Section Heading` heading — used to tag the section each rule
# sits under.
SECTION_RE = re.compile(r"^##\s+(.+?)\s*$")

# Matches a `Source: <url>` line; captures the URL (everything after the
# whitespace following `Source:`). Intentionally permissive — the URL may
# be a bare GitHub URL or a `https://... — hand-transcribed in ...` line,
# and both forms resolve to a real source. We keep the full tail for
# auditability.
SOURCE_RE = re.compile(r"^Source:\s+(\S+.*?)\s*$")

# Markdown table cells that contain `|` need escaping, and newlines must
# be squashed — we truncate claim text at 80 chars as the spec asks.
MAX_CLAIM_LEN = 80

# Kinds we recognize; used to sort deterministically. `Hygiene` rows sort
# after Idioms so the provenance table groups Rules → Idioms → Hygiene
# within each file/section tuple.
KIND_ORDER = {"Rule": 0, "Idiom": 1, "Hygiene": 2}


@dataclass(frozen=True, order=True)
class ProvenanceRow:
    """One row in the provenance table. Declaration order drives
    tuple-based sort: file, section, rule_num, kind, claim."""

    sort_file: str
    sort_section: str
    sort_rule_num: int
    sort_kind: int
    sort_claim: str
    # Display fields (not part of sort key — but included so the
    # dataclass equality is safe).
    file: str
    section: str
    kind: str
    rule_num_display: str
    claim: str
    source: str
    last_verified: str


def _escape_cell(text: str) -> str:
    """Escape a value for a markdown table cell."""
    return text.replace("|", "\\|").replace("\n", " ").strip()


def _truncate_claim(heading_text: str) -> str:
    """Trim the Rule/Idiom/Hygiene heading text to MAX_CLAIM_LEN chars,
    keeping an explicit ellipsis when truncated."""
    heading_text = heading_text.strip()
    if len(heading_text) <= MAX_CLAIM_LEN:
        return heading_text
    return heading_text[: MAX_CLAIM_LEN - 1].rstrip() + "…"


def _extract_source(lines: list[str], start: int, window: int = 5) -> str:
    """Scan up to `window` lines after `start` for a `Source:` line.

    Returns the URL (possibly followed by a hand-transcription note) or
    the empty string if not found.
    """
    end = min(start + 1 + window, len(lines))
    for i in range(start + 1, end):
        match = SOURCE_RE.match(lines[i])
        if match:
            return match.group(1).strip()
    return ""


def scan_reference(path: Path) -> list[ProvenanceRow]:
    """Walk a single reference file, yielding one ProvenanceRow per
    `### Rule`, `### Idiom`, or `### Hygiene` heading."""
    fm = load_frontmatter(path)
    last_verified = str(fm.get("last_reviewed", "unknown"))

    body = body_after_frontmatter(path)
    lines = body.splitlines()

    rows: list[ProvenanceRow] = []
    current_section = "(no section)"

    for idx, line in enumerate(lines):
        sec = SECTION_RE.match(line)
        if sec:
            current_section = sec.group(1).strip()
            continue

        head = HEADING_RE.match(line)
        if not head:
            continue

        kind = head.group(1)
        rule_num_str = head.group(2) or ""
        # Sort Idioms after Rules within a section; unnumbered items sort
        # by claim text so output is deterministic.
        sort_rule_num = int(rule_num_str) if rule_num_str else 10_000

        full_heading_text = head.group(3).strip()
        claim = _truncate_claim(full_heading_text)
        source = _extract_source(lines, idx)

        row = ProvenanceRow(
            sort_file=path.name,
            sort_section=current_section,
            sort_rule_num=sort_rule_num,
            sort_kind=KIND_ORDER[kind],
            sort_claim=claim.lower(),
            file=path.name,
            section=current_section,
            kind=kind,
            rule_num_display=rule_num_str if rule_num_str else "—",
            claim=claim,
            source=source,
            last_verified=last_verified,
        )
        rows.append(row)

    return rows


def collect_all_rows() -> list[ProvenanceRow]:
    """Walk every `references/*.md` file, sorted by filename."""
    files = sorted(REFERENCES_DIR.glob("*.md"))
    rows: list[ProvenanceRow] = []
    for f in files:
        rows.extend(scan_reference(f))
    rows.sort()
    return rows


def render_markdown(rows: list[ProvenanceRow]) -> str:
    """Render the sorted rows as a markdown document."""
    header = [
        "# Rule Provenance",
        "",
        (
            "Audit trail for every `### Rule`, `### Idiom`, and `### Hygiene` "
            "heading in `references/*.md`. Each row records the rule's source URL and "
            "the `last_reviewed` date from the reference file's frontmatter. "
            "This file is auto-generated — do not edit by hand."
        ),
        "",
        (
            "Regenerate after editing any reference file:"
        ),
        "",
        "```bash",
        "uv --directory pipeline run python make_provenance.py > docs/rule-provenance.md",
        "```",
        "",
        "| File | Section | # | Claim | Source | Last verified |",
        "|------|---------|---|-------|--------|---------------|",
    ]

    body: list[str] = []
    for r in rows:
        # Tag the `#` column so Rules, Idioms, and Hygiene items remain
        # visually distinguishable in the table even though `Kind` is not
        # a separate column: Rules carry their number (`1`..`20`), Idioms
        # carry `idiom`, Hygiene items carry `H<n>` (so `H1` sorts near
        # `1` alphabetically while still flagging the demoted-Rule kind).
        if r.kind == "Rule":
            num_display = r.rule_num_display
        elif r.kind == "Hygiene":
            num_display = f"H{r.rule_num_display}" if r.rule_num_display != "—" else "hygiene"
        else:
            num_display = "idiom"
        body.append(
            "| {file} | {section} | {num} | {claim} | {source} | {lv} |".format(
                file=_escape_cell(r.file),
                section=_escape_cell(r.section),
                num=_escape_cell(num_display),
                claim=_escape_cell(r.claim),
                source=_escape_cell(r.source),
                lv=_escape_cell(r.last_verified),
            )
        )

    footer = [
        "",
        f"Total rows: {len(rows)}.",
        "",
    ]

    return "\n".join(header + body + footer)


def main() -> int:
    rows = collect_all_rows()

    # Fail loud if any Rule/Idiom/Hygiene heading lacks a Source URL
    # within the 5-line window — silent empty `source` cells are the
    # single most destructive failure mode for an audit trail.
    missing = [r for r in rows if not r.source]
    if missing:
        sys.stderr.write(
            f"ERROR: {len(missing)} Rule/Idiom/Hygiene heading(s) lack a Source URL within 5 lines:\n"
        )
        for r in sorted(missing, key=lambda r: (r.file, r.section, r.claim)):
            sys.stderr.write(f"  - {r.file} | {r.section} | {r.claim}\n")
        sys.stderr.write(
            "\nAdd a 'Source: <URL>' line within 5 lines after the heading, then re-run.\n"
        )
        sys.exit(1)

    sys.stdout.write(render_markdown(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
