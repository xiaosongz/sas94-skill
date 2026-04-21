"""Build a construct index from SAS 9.4 docset markdown.

Scans ``pipeline/cache/docs/<docset>.md`` (produced by fetch_sas_pdfs.py
via markitdown or pymupdf) for dictionary-style headings such as
"%MACRO Macro Statement", "ARRAY Statement", "SCAN Function", or
"The MEANS Procedure", and emits a structured JSON keyed by canonical
construct name.

Downstream consumers:
  * T11 — Quick Ref Doc URL filling (macros.md, data-step.md)
  * T12-T15 — reference-file population (procs, ods, formats, functions)

Run:
    uv run python pipeline/extractors/sas_pdf_index.py
"""

from __future__ import annotations

import json
import re
import sys
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

PIPELINE_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = PIPELINE_DIR / "cache" / "docs"
EXTRACTED_DIR = PIPELINE_DIR / "cache" / "extracted"
MANIFEST_PATH = EXTRACTED_DIR / "sas_pdfs_manifest.json"
OUT_PATH = EXTRACTED_DIR / "sas_docs.json"

# We rely on the static extraction date from the manifest rather than
# today's date so the output is reproducible.
_MANIFEST_SCRAPED_AT_FALLBACK = "1970-01-01"

Category = Literal[
    "macro-statement",
    "macro-function",
    "data-step-statement",
    "procedure",
    "function",
    "format",
    "informat",
    "ods-statement",
]


class SasDocEntry(BaseModel):
    name: str
    docset: str
    category: Category
    canonical_url: str
    syntax_excerpt: str | None
    short_description: str | None
    markdown_path: str
    approx_line_in_md: int


class SasDocsIndex(BaseModel):
    source: str = (
        "pipeline/cache/docs/*.md via markitdown / pymupdf (fetch_sas_pdfs.py)"
    )
    extracted_at: str
    entries: list[SasDocEntry]
    per_docset_counts: dict[str, int]
    notes: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Heuristics configuration
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DocsetPattern:
    """One heading regex and the category it resolves to.

    ``name_transform`` lets us canonicalize the captured group (e.g.
    strip ``w.``/``w.d`` suffix from format names, uppercase macro
    statements).
    """

    regex: re.Pattern[str]
    category: Category
    # Optional post-processor on the captured name.
    name_transform: Callable[[str], str] | None = None


def _upper(s: str) -> str:
    return s.upper()


def _strip_format_suffix(s: str) -> str:
    """Drop ``w.`` / ``w.d`` / trailing dot from format/informat names.

    Examples: ``$CHARw.`` -> ``$CHAR``; ``MMDDYYw.`` -> ``MMDDYY``;
    ``$N8601Bw.d`` -> ``$N8601B``.
    """
    s = re.sub(r"w\.d$", "", s)
    s = re.sub(r"w\.$", "", s)
    s = s.rstrip(".")
    return s


# Heading regex catalog per docset. Ordering matters within a docset:
# the first pattern that matches a given line wins, so list more
# specific patterns before the more general ones.
PATTERNS_BY_DOCSET: dict[str, list[DocsetPattern]] = {
    "mcrolref": [
        DocsetPattern(
            re.compile(r"^(%\w+)\s+Autocall Macro$"),
            "macro-function",
            _upper,
        ),
        # "%SYSFUNC, %QSYSFUNC Macro Functions" — comma-separated
        # compound heading. Capture the first %-token as canonical name.
        DocsetPattern(
            re.compile(r"^(%\w+)(?:,\s*%\w+)+\s+Macro Functions?$"),
            "macro-function",
            _upper,
        ),
        DocsetPattern(
            re.compile(r"^(%\w+)\s+Macro Functions?$"),
            "macro-function",
            _upper,
        ),
        DocsetPattern(
            re.compile(r"^(%\w+)\s+Function$"),
            "macro-function",
            _upper,
        ),
        # Compound macro statements: %IF-%THEN/%ELSE, %DO %WHILE, etc.
        # Capture the leading token (first %-word) as canonical name.
        DocsetPattern(
            re.compile(
                r"^(%\w+(?:[-\s/]+%?\w+)*)\s+Macro Statement$"
            ),
            "macro-statement",
            _upper,
        ),
        DocsetPattern(
            re.compile(r"^(CALL\s+\w+)\s+Routine$"),
            "macro-statement",
            _upper,
        ),
    ],
    "lestmtsref": [
        # Compound/qualified statements e.g. "IF-THEN/ELSE Statement",
        # "IF Statement: Subsetting", "FILE Statement, CAS Engine".
        # Accept a broad heading shape so we capture these, then
        # canonicalize by keeping everything up to the last "Statement".
        DocsetPattern(
            re.compile(r"^([A-Z][A-Z0-9][A-Z0-9\-/]*)\s+Statement(?::\s+\w+)?$"),
            "data-step-statement",
            _upper,
        ),
        DocsetPattern(
            re.compile(r"^([A-Z][A-Z0-9]*)\s+Statement$"),
            "data-step-statement",
            _upper,
        ),
        # Lowercase first word + Statement (e.g., "Assignment Statement",
        # "Comment Statement", "Null Statement") are concept entries;
        # we accept them as data-step-statement too.
        DocsetPattern(
            re.compile(r"^([A-Z][a-z]+)\s+Statement$"),
            "data-step-statement",
        ),
    ],
    "lefunctionsref": [
        # Functions with qualifiers e.g. "SUBSTR (left of =) Function".
        # Capture the leading identifier only.
        DocsetPattern(
            re.compile(r"^([A-Z][A-Z0-9]*)\s*\([^)]+\)\s+Function$"),
            "function",
            _upper,
        ),
        DocsetPattern(
            re.compile(r"^([A-Z][A-Z0-9]*)\s+Function$"),
            "function",
            _upper,
        ),
        DocsetPattern(
            re.compile(r"^(CALL\s+[A-Z][A-Z0-9]*)\s+Routine$"),
            "function",
            _upper,
        ),
    ],
    "leforinforref": [
        DocsetPattern(
            re.compile(r"^([A-Z\$][A-Z0-9\$]*w?\.?d?)\s+Format$"),
            "format",
            _strip_format_suffix,
        ),
        DocsetPattern(
            re.compile(r"^([A-Z\$][A-Z0-9\$]*w?\.?d?)\s+Informat$"),
            "informat",
            _strip_format_suffix,
        ),
    ],
    "proc": [
        # Chapter-level heading is the preferred anchor (matches the
        # bulk of base procedures). Accept "PROC X" and "The X"
        # variants as fallbacks for a handful of appendix / What's
        # New cross-references.
        DocsetPattern(
            re.compile(r"^([A-Z][A-Z0-9_]*)\s+Procedure$"),
            "procedure",
            _upper,
        ),
        DocsetPattern(
            re.compile(r"^PROC\s+(\w+)\s+Procedure$"),
            "procedure",
            _upper,
        ),
        DocsetPattern(
            re.compile(r"^The\s+(\w+)\s+Procedure$"),
            "procedure",
            _upper,
        ),
    ],
    "odsug": [
        DocsetPattern(
            re.compile(r"^(ODS\s+\w+(?:\s+\w+)?)\s+Statement$"),
            "ods-statement",
            _upper,
        ),
    ],
    "statug": [
        DocsetPattern(
            re.compile(r"^The\s+([A-Z][A-Z0-9_]*)\s+Procedure$"),
            "procedure",
            _upper,
        ),
        DocsetPattern(
            re.compile(r"^PROC\s+([A-Z][A-Z0-9_]*)\s+Procedure$"),
            "procedure",
            _upper,
        ),
        DocsetPattern(
            re.compile(r"^([A-Z][A-Z0-9_]*)\s+Procedure$"),
            "procedure",
            _upper,
        ),
    ],
    # lepg is narrative Programmer's Guide Essentials — no dictionary
    # entries to scrape; we intentionally skip it and document that in
    # the output ``notes`` field.
}


# ---------------------------------------------------------------------------
# Line classification helpers
# ---------------------------------------------------------------------------


# TOC lines look like: "%ABORT Macro Statement . . . . . 378".
_TOC_DOTS_RE = re.compile(r"\.\s\.")
# Page-header lines look like: "%ABORT Macro Statement 379" — heading
# text followed by 1-4 digits and nothing else.
_TRAILING_PAGENUM_RE = re.compile(r"\s+\d{1,4}$")


def _is_noise_line(line: str) -> bool:
    """Return True if ``line`` is a TOC entry or page header repeat."""
    if _TOC_DOTS_RE.search(line):
        return True
    if _TRAILING_PAGENUM_RE.search(line):
        return True
    return False


def _match_heading(
    line: str, patterns: list[DocsetPattern]
) -> tuple[str, Category] | None:
    """Try each pattern; return ``(canonical_name, category)`` on first hit."""
    for pat in patterns:
        m = pat.regex.match(line)
        if not m:
            continue
        # Prefer a named captured group; else pick the first non-None group.
        groups = [g for g in m.groups() if g]
        if not groups:
            continue
        raw = groups[0]
        name = pat.name_transform(raw) if pat.name_transform else raw
        return name, pat.category
    return None


# ---------------------------------------------------------------------------
# Excerpt extraction
# ---------------------------------------------------------------------------


_SYNTAX_HEADER_RE = re.compile(r"^Syntax\s*:?\s*$", re.IGNORECASE)
_DESC_HEADER_RE = re.compile(r"^Description\s*:?\s*$", re.IGNORECASE)

# Skip lines that are obviously boilerplate metadata ("Valid in:",
# "Category:", etc.) when hunting for the first prose paragraph.
_METADATA_PREFIXES = (
    "Type:",
    "Valid in:",
    "Valid In:",
    "Category:",
    "Categories:",
    "Restriction:",
    "Restrictions:",
    "Requirement:",
    "Requirements:",
    "Default:",
    "Interaction:",
    "Interactions:",
    "Note:",
    "Tip:",
    "See:",
    "See also:",
    "Alias:",
    "Aliases:",
    "Support:",
    "CAS:",
    "Data source:",
    "Restrictions",
    "Tips:",
)


def _words_truncate(text: str, max_words: int) -> str:
    """Truncate ``text`` to ``max_words`` whitespace-separated tokens."""
    toks = text.split()
    if len(toks) <= max_words:
        return text.strip()
    return " ".join(toks[:max_words]).rstrip(",;:") + "..."


def _find_syntax_excerpt(
    lines: list[str], heading_idx: int, lookahead: int = 40
) -> str | None:
    """Return the first non-blank content block after a 'Syntax' header.

    ``lookahead`` lines are scanned beyond ``heading_idx``. The excerpt
    is truncated to ~30 words. Returns None if no Syntax header or no
    subsequent non-blank content.
    """
    end = min(heading_idx + lookahead, len(lines))
    i = heading_idx + 1
    while i < end:
        if _SYNTAX_HEADER_RE.match(lines[i].strip()):
            # Found the Syntax header: skip blanks, take the next
            # contiguous non-blank block.
            j = i + 1
            while j < end and not lines[j].strip():
                j += 1
            block: list[str] = []
            while j < end and lines[j].strip():
                # Stop at sub-headers like "Required Arguments" or
                # "Arguments" which typically follow the syntax.
                stripped = lines[j].strip()
                if (
                    stripped.endswith(":")
                    and len(stripped) < 40
                    and not stripped.startswith(("<", "/"))
                ):
                    break
                block.append(stripped)
                j += 1
            if not block:
                return None
            text = " ".join(block)
            return _words_truncate(text, 30)
        i += 1
    return None


def _find_short_description(
    lines: list[str], heading_idx: int, lookahead: int = 30
) -> str | None:
    """Return the first non-boilerplate prose line(s) after the heading.

    Walks forward from ``heading_idx + 1``, skipping blank lines,
    metadata prefixes (``Type:`` / ``Valid in:`` etc.), TOC-style
    dotted lines, and short section-label lines that end in ``:``,
    then takes the next contiguous prose paragraph and truncates to
    ~50 words.
    """
    end = min(heading_idx + lookahead, len(lines))
    i = heading_idx + 1

    # Advance cursor over any sequence of lines we consider "skippable"
    # before the real description.
    def _skippable(ln: str) -> bool:
        if not ln:
            return True
        if _is_noise_line(ln):
            return True
        # A short label like "Valid in:" or "Syntax" (no colon) is a
        # metadata section header; skip it and the immediate value that
        # follows will still look like prose, but we drop those with
        # the metadata prefix test below.
        if ln.startswith(_METADATA_PREFIXES):
            return True
        # Chapter-internal TOC lines in base procedures follow the form
        # "Overview: MEANS Procedure" (on its own, with dots already
        # filtered) or "PROC MEANS Statement" (short label ending in
        # "Statement"/"Procedure") that dot-filtered but aren't real
        # prose. Skip these.
        if re.match(r"^[A-Z][\w /:]{0,60}(Procedure|Statement)$", ln):
            return True
        # Short single-token/phrase labels ending in a colon (e.g.
        # "Valid in:", "Categories:").
        if ln.endswith(":") and len(ln) < 32:
            return True
        return False

    while i < end and _skippable(lines[i].strip()):
        i += 1
    if i >= end:
        return None
    first = lines[i].strip()
    if _SYNTAX_HEADER_RE.match(first) or _DESC_HEADER_RE.match(first):
        return None
    # Looks like prose — gather the contiguous block.
    block: list[str] = []
    while i < end and lines[i].strip():
        stripped = lines[i].strip()
        if stripped.startswith(_METADATA_PREFIXES):
            break
        if _SYNTAX_HEADER_RE.match(stripped):
            break
        block.append(stripped)
        i += 1
    if not block:
        return None
    text = " ".join(block)
    # Drop trailing page-number noise if it snuck in.
    text = re.sub(r"\s+\d{1,4}$", "", text)
    return _words_truncate(text, 50) or None


# ---------------------------------------------------------------------------
# Core extraction
# ---------------------------------------------------------------------------


def _canonical_url(docset: str) -> str:
    return f"https://documentation.sas.com/doc/en/{docset}/9.4/{docset}.htm"


def _load_manifest() -> dict:
    with MANIFEST_PATH.open() as fh:
        return json.load(fh)


def _extract_from_docset(
    docset: str, md_path_rel: str
) -> tuple[list[SasDocEntry], list[str]]:
    """Scan ``pipeline/cache/docs/<docset>.md`` and return entries + notes."""
    patterns = PATTERNS_BY_DOCSET.get(docset)
    if patterns is None:
        return [], [f"{docset}: intentionally skipped (narrative guide, no dictionary entries)"]

    # Anchor the read on the repo-root-relative path stored in the manifest.
    repo_root = PIPELINE_DIR.parent
    abs_md = repo_root / md_path_rel
    if not abs_md.exists():
        return [], [f"{docset}: markdown not found at {md_path_rel}"]

    text = abs_md.read_text(encoding="utf-8", errors="replace")
    # Use explicit `\n` split (NOT str.splitlines) because some PDF-to-md
    # conversions leave form-feed (``\x0c``) characters in the markdown
    # and ``str.splitlines`` treats those as line terminators too.
    # That would desynchronize the 1-indexed ``approx_line_in_md`` from
    # the line numbering seen by ``grep -n``, ``awk``, and editors.
    lines = text.split("\n")

    # Pass 1: collect every potential heading hit with its line number
    # and the description/syntax it would produce. Then pick one per
    # canonical name, preferring hits that have a Syntax section nearby
    # (those are the real dictionary chapters, not preface/TOC
    # cross-references).
    candidates: dict[str, list[SasDocEntry]] = {}

    for idx, raw in enumerate(lines):
        line = raw.rstrip()
        if not line:
            continue
        if _is_noise_line(line):
            continue
        hit = _match_heading(line, patterns)
        if hit is None:
            continue
        name, category = hit
        if not name:
            continue

        description = _find_short_description(lines, idx)
        syntax = _find_syntax_excerpt(lines, idx)

        candidates.setdefault(name, []).append(
            SasDocEntry(
                name=name,
                docset=docset,
                category=category,
                canonical_url=_canonical_url(docset),
                syntax_excerpt=syntax,
                short_description=description,
                markdown_path=md_path_rel,
                approx_line_in_md=idx + 1,  # 1-indexed
            )
        )

    # Pass 2: pick the best candidate per name. Preference order:
    #   1. has a syntax_excerpt AND a short_description
    #   2. has a short_description
    #   3. first occurrence
    entries: list[SasDocEntry] = []
    notes: list[str] = []
    for name, cand_list in candidates.items():
        best = max(
            cand_list,
            key=lambda e: (
                e.syntax_excerpt is not None,
                e.short_description is not None,
                # Prefer the earlier line if tied; negate to turn argmax
                # into argmin on line number.
                -e.approx_line_in_md,
            ),
        )
        entries.append(best)

    if not entries:
        notes.append(f"{docset}: 0 entries matched — patterns may need tuning")

    return entries, notes


def build_index() -> SasDocsIndex:
    manifest = _load_manifest()
    ok_docsets = [d for d in manifest.get("docsets", []) if d.get("status") == "ok"]
    extracted_at = manifest.get("scraped_at") or _MANIFEST_SCRAPED_AT_FALLBACK

    all_entries: list[SasDocEntry] = []
    per_docset_counts: dict[str, int] = {}
    notes: list[str] = []

    for d in ok_docsets:
        name = d["name"]
        md_path = d["md_path"]
        entries, docset_notes = _extract_from_docset(name, md_path)
        per_docset_counts[name] = len(entries)
        all_entries.extend(entries)
        notes.extend(docset_notes)

    # Deterministic order for idempotent output.
    all_entries.sort(key=lambda e: (e.docset, e.category, e.name))

    return SasDocsIndex(
        extracted_at=extracted_at,
        entries=all_entries,
        per_docset_counts=per_docset_counts,
        notes=notes,
    )


def _round_trip_validate(index: SasDocsIndex) -> SasDocsIndex:
    """Validate that model_dump -> model_validate preserves the index."""
    dumped = index.model_dump()
    return SasDocsIndex.model_validate(dumped)


def main() -> int:
    if not MANIFEST_PATH.exists():
        raise SystemExit(f"manifest not found: {MANIFEST_PATH}")
    if not DOCS_DIR.exists():
        raise SystemExit(f"docs dir not found: {DOCS_DIR}")

    # Sanity: the manifest should record 'scraped_at' as an ISO date;
    # if not, fall back to today's date.
    index = build_index()
    if index.extracted_at == _MANIFEST_SCRAPED_AT_FALLBACK:
        index = index.model_copy(update={"extracted_at": date.today().isoformat()})

    # Round-trip validation per success criterion 6.
    index = _round_trip_validate(index)

    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)
    payload = index.model_dump()
    OUT_PATH.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    total = len(index.entries)
    print(f"wrote {OUT_PATH} ({total} entries)")
    print("  per-docset counts:")
    for docset in sorted(index.per_docset_counts):
        print(f"    {docset}: {index.per_docset_counts[docset]}")
    if index.notes:
        print("  notes:")
        for note in index.notes:
            print(f"    - {note}")

    if total < 40:
        raise SystemExit(
            f"only {total} entries extracted; expected >=40. "
            "Heading patterns may need tuning."
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
