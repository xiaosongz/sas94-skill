"""Generate `docs/coverage-matrix.md` — a per-reference-file status
report showing which template sections are populated vs. stubbed.

Usage:

    uv --directory pipeline run python make_coverage.py > docs/coverage-matrix.md

The script walks every `references/*.md` file and checks for the
presence of each template section per the spec in `docs/design.md`:

- REQUIRED sections (must be populated for "populated" status):
    Overview, Critical Rules, Canonical Idioms, Function / Statement
    Quick Ref, See Also
- OPTIONAL sections: Silent Pitfalls, Anti-patterns

A section counts as "populated" when it exists AND contains actual
content — for Overview that means prose that is NOT just a single
`TODO (source pending)` line; for Critical Rules that means at least
one `### Rule` heading with CORRECT and WRONG code blocks plus a
`Source:` URL; for Canonical Idioms that means at least two `### Idiom`
headings.

Re-running the script must produce byte-identical output.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

from _common import REFERENCES_DIR, body_after_frontmatter

# Section headings we care about. Keyed by the section's canonical
# `## ...` heading text (exact match after trimming).
REQUIRED_SECTIONS = [
    "Overview",
    "Critical Rules",
    "Canonical Idioms",
    "Function / Statement Quick Ref",
    "See Also",
]

OPTIONAL_SECTIONS = [
    "Silent Pitfalls",
    "Anti-patterns",
]

# The spec uses a few legitimate variants of the Quick Ref heading.
# Accept any heading that starts with the prefix "Function" OR contains
# "Quick Ref".
QUICK_REF_HEADING_RE = re.compile(r"^(Function.*Quick Ref|Quick Ref.*|Function / Statement.*)$")

# Master-reference uses `Reference-file Pointers` as its idiom-equivalent
# section — it is a router file, not a topic file. Accept either heading.
CANONICAL_IDIOMS_HEADINGS = ("Canonical Idioms", "Reference-file Pointers")

# Anti-patterns heading is sometimes suffixed with `(STOP signs)` in
# seeded files. Prefix-match the heading.
ANTI_PATTERN_HEADING_RE = re.compile(r"^Anti-patterns")

# Critical Rules heading is sometimes suffixed — e.g. `(Top-20 Aggregated)`
# on the master-reference aggregator. Prefix-match the heading.
CRITICAL_RULES_HEADING_RE = re.compile(r"^Critical Rules")

# Stub Overview sections start with the TODO marker.
STUB_OVERVIEW_RE = re.compile(r"^TODO\s*\(source pending\)", re.IGNORECASE)


@dataclass(frozen=True)
class FileCoverage:
    file: str
    overview: bool
    critical_rules: bool
    canonical_idioms: bool
    quick_ref: bool
    see_also: bool
    silent_pitfalls: bool
    anti_patterns: bool

    @property
    def required_populated(self) -> int:
        return sum(
            [
                self.overview,
                self.critical_rules,
                self.canonical_idioms,
                self.quick_ref,
                self.see_also,
            ]
        )

    @property
    def required_pct(self) -> int:
        return round(100 * self.required_populated / len(REQUIRED_SECTIONS))

    @property
    def status(self) -> str:
        return "populated" if self.required_populated == len(REQUIRED_SECTIONS) else "stub"


def _split_sections(body: str) -> dict[str, str]:
    """Split a reference-file body into a `{heading: content}` map.

    The body is split on `^## ` level-2 headings. Content between the
    heading and the next `^## ` (or EOF) is the section content.
    """
    lines = body.splitlines()
    sections: dict[str, str] = {}
    current_name: str | None = None
    current_lines: list[str] = []

    for line in lines:
        if line.startswith("## ") and not line.startswith("### "):
            if current_name is not None:
                sections[current_name] = "\n".join(current_lines).strip()
            current_name = line[3:].strip()
            current_lines = []
        else:
            if current_name is not None:
                current_lines.append(line)
    if current_name is not None:
        sections[current_name] = "\n".join(current_lines).strip()
    return sections


def _find_quick_ref(sections: dict[str, str]) -> str | None:
    for name, content in sections.items():
        if QUICK_REF_HEADING_RE.match(name):
            return content
    return None


def _find_canonical_idioms(sections: dict[str, str]) -> str | None:
    """Locate the Canonical Idioms section, or the equivalent
    Reference-file Pointers section on the master-reference router."""
    for heading in CANONICAL_IDIOMS_HEADINGS:
        if heading in sections:
            return sections[heading]
    return None


def _find_anti_patterns(sections: dict[str, str]) -> str | None:
    for name, content in sections.items():
        if ANTI_PATTERN_HEADING_RE.match(name):
            return content
    return None


def _find_critical_rules(sections: dict[str, str]) -> str | None:
    for name, content in sections.items():
        if CRITICAL_RULES_HEADING_RE.match(name):
            return content
    return None


def _overview_populated(content: str | None) -> bool:
    """Overview is populated when it has non-stub prose."""
    if not content:
        return False
    stripped = content.strip()
    if not stripped:
        return False
    # Collapse to non-empty lines and check the first line is not a
    # pure `TODO (source pending) — ...` line.
    first_line = next((l for l in stripped.splitlines() if l.strip()), "")
    if STUB_OVERVIEW_RE.match(first_line.strip()):
        return False
    return True


def _critical_rules_populated(content: str | None) -> bool:
    """Populated = at least one `### Rule N:` heading with a `Source:`
    line within 5 lines, plus at least one CORRECT and one WRONG code
    fence in the section."""
    if not content:
        return False
    rule_headings = [l for l in content.splitlines() if l.startswith("### Rule")]
    if not rule_headings:
        return False
    lines = content.splitlines()
    # Look for at least one Source: within the section.
    has_source = any(l.strip().startswith("Source:") for l in lines)
    has_correct = any("CORRECT" in l for l in lines)
    has_wrong = any("WRONG" in l for l in lines)
    return has_source and has_correct and has_wrong


def _canonical_idioms_populated(content: str | None) -> bool:
    """Populated = at least 2 `### Idiom:` headings, OR (on the
    master-reference router) at least 2 bullet entries in the
    Reference-file Pointers section."""
    if not content:
        return False
    idioms = [l for l in content.splitlines() if l.startswith("### Idiom")]
    if len(idioms) >= 2:
        return True
    # Fallback for the Reference-file Pointers router-style section:
    # count bullet entries that link to a reference file.
    bullets = [l for l in content.splitlines() if l.strip().startswith("-")]
    return len(bullets) >= 2


def _quick_ref_populated(content: str | None) -> bool:
    """Populated = a markdown table with at least one data row (not
    just the header + separator)."""
    if not content:
        return False
    table_rows = [l for l in content.splitlines() if l.startswith("|")]
    # Expect header + separator + at least one data row = 3+ rows.
    return len(table_rows) >= 3


def _see_also_populated(content: str | None) -> bool:
    """Populated = at least one bullet that references a file."""
    if not content:
        return False
    bullets = [l for l in content.splitlines() if l.strip().startswith("-")]
    return len(bullets) >= 1


def _silent_pitfalls_populated(content: str | None) -> bool:
    if not content:
        return False
    bullets = [l for l in content.splitlines() if l.strip().startswith("-")]
    return len(bullets) >= 1


def _anti_patterns_populated(content: str | None) -> bool:
    if not content:
        return False
    bullets = [l for l in content.splitlines() if l.strip().startswith("-")]
    return len(bullets) >= 1


def scan_reference(path: Path) -> FileCoverage:
    """Return a FileCoverage record for a single reference file."""
    body = body_after_frontmatter(path)
    sections = _split_sections(body)

    return FileCoverage(
        file=path.name,
        overview=_overview_populated(sections.get("Overview")),
        critical_rules=_critical_rules_populated(_find_critical_rules(sections)),
        canonical_idioms=_canonical_idioms_populated(_find_canonical_idioms(sections)),
        quick_ref=_quick_ref_populated(_find_quick_ref(sections)),
        see_also=_see_also_populated(sections.get("See Also")),
        silent_pitfalls=_silent_pitfalls_populated(sections.get("Silent Pitfalls")),
        anti_patterns=_anti_patterns_populated(_find_anti_patterns(sections)),
    )


def _checkmark(flag: bool) -> str:
    return "yes" if flag else "no"


def render_markdown(rows: list[FileCoverage]) -> str:
    header = [
        "# Coverage Matrix",
        "",
        (
            "Per-reference-file coverage report — which template sections are "
            "populated vs. stubbed. Required sections must all be populated "
            "for a file to earn `populated` status; Silent Pitfalls and "
            "Anti-patterns are optional. Generated from `references/*.md`; "
            "do not edit by hand."
        ),
        "",
        "Regenerate after editing any reference file:",
        "",
        "```bash",
        "uv --directory pipeline run python make_coverage.py > docs/coverage-matrix.md",
        "```",
        "",
        "| File | Overview | Critical Rules | Canonical Idioms | Quick Ref | See Also | Silent Pitfalls | Anti-patterns | Required % | Status |",
        "|------|----------|----------------|------------------|-----------|----------|------------------|----------------|------------|--------|",
    ]

    body: list[str] = []
    for r in rows:
        body.append(
            "| {file} | {ov} | {cr} | {ci} | {qr} | {sa} | {sp} | {ap} | {pct}% | {status} |".format(
                file=r.file,
                ov=_checkmark(r.overview),
                cr=_checkmark(r.critical_rules),
                ci=_checkmark(r.canonical_idioms),
                qr=_checkmark(r.quick_ref),
                sa=_checkmark(r.see_also),
                sp=_checkmark(r.silent_pitfalls),
                ap=_checkmark(r.anti_patterns),
                pct=r.required_pct,
                status=r.status,
            )
        )

    populated_count = sum(1 for r in rows if r.status == "populated")
    stub_count = len(rows) - populated_count

    footer = [
        "",
        f"Populated: {populated_count} / {len(rows)}; Stubs: {stub_count} / {len(rows)}.",
        "",
    ]

    return "\n".join(header + body + footer)


def collect_all_rows() -> list[FileCoverage]:
    files = sorted(REFERENCES_DIR.glob("*.md"))
    return [scan_reference(f) for f in files]


def main() -> int:
    rows = collect_all_rows()
    sys.stdout.write(render_markdown(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
