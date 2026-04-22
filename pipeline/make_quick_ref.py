"""Fill `TODO (source pending)` cells in the "Function / Statement Quick Ref"
tables of `references/macros.md` and `references/data-step.md`.

Reads `pipeline/cache/extracted/sas_docs.json` (1217 constructs indexed by
`pipeline/extractors/sas_pdf_index.py` from the SAS 9.4 docset PDFs) and
replaces every `TODO (source pending)` cell whose first-column name matches
a known construct with `[<name>](<canonical_url>)` where `<name>` is the
original first-cell text (preserving backticks) and `<canonical_url>` is
the docset landing page from the index entry.

Rows whose construct is not indexed (e.g. `_N_`, `_ERROR_` are automatic
variables, not statements — they have no landing page in `lestmtsref.pdf`)
keep the TODO marker. We do not fabricate URLs.

Usage:

    cd pipeline && uv run python make_quick_ref.py

Idempotent — re-running produces no diff. Writes atomically (tempfile +
rename) so a crash mid-write cannot corrupt the reference files.

Exit 0 on success (regardless of unfilled TODOs — those are legit). Exit 1
only on fatal errors (missing index, parse failures).
"""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = REPO_ROOT / "pipeline" / "cache" / "extracted" / "sas_docs.json"
REFERENCES_DIR = REPO_ROOT / "plugins" / "sas94" / "skills" / "sas94" / "references"

TODO_MARKER = "TODO (source pending)"

# Quick Ref table header — we only rewrite cells under a table that starts
# with this pipe-prefixed header row. Any other pipe-delimited table is
# left untouched (future-proofs against us adding more tables later).
QUICK_REF_HEADER = "| Name | Syntax | Purpose | Common mistake | Doc URL |"


@dataclass(frozen=True)
class Construct:
    """One entry from sas_docs.json, trimmed to what we need for linking."""

    name: str
    category: str
    canonical_url: str


# Category preference per reference file. When a lookup key resolves to
# multiple Construct entries (e.g. `FORMAT` is both a data-step statement
# and a PROC), we pick the highest-priority category for that file.
#
# Rationale: the Quick Ref tables are scoped to their file's domain, so
# `references/data-step.md` should link `format` to the FORMAT statement
# in `lestmtsref`, not the FORMAT procedure in `proc`.
CATEGORY_PRIORITY: dict[str, list[str]] = {
    "macros.md": [
        "macro-statement",
        "macro-function",
        "function",
        "data-step-statement",
        "procedure",
        "format",
        "informat",
        "ods-statement",
    ],
    "data-step.md": [
        "data-step-statement",
        "function",
        "macro-statement",
        "macro-function",
        "procedure",
        "format",
        "informat",
        "ods-statement",
    ],
}


def _normalize(name: str) -> str:
    """Canonicalize a construct name for index lookup.

    - lowercase
    - strip backticks, backslashes, leading/trailing whitespace
    - collapse internal whitespace runs to a single space

    Leaves `%` prefix intact so `%let` does not collide with `let` (there
    is no bare `let` in SAS but keeping the distinction is safer).
    """
    s = name.strip().lower()
    s = s.replace("`", "").replace("\\", "")
    s = re.sub(r"\s+", " ", s)
    return s


def load_index() -> list[Construct]:
    if not INDEX_PATH.exists():
        sys.stderr.write(
            f"ERROR: construct index missing at {INDEX_PATH}\n"
            "Run `pipeline/extractors/sas_pdf_index.py` first.\n"
        )
        sys.exit(1)

    data = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    entries = data.get("entries") or []
    out: list[Construct] = []
    for e in entries:
        name = e.get("name")
        url = e.get("canonical_url")
        cat = e.get("category") or ""
        if not name or not url:
            continue
        out.append(Construct(name=name, category=cat, canonical_url=url))
    return out


def build_lookup(
    index: Iterable[Construct],
) -> dict[str, list[Construct]]:
    """Group constructs by normalized lookup key.

    A single entry may be registered under multiple keys — e.g. `%IF-%THEN/%ELSE`
    is reachable via `%if`, `%then`, `%else`, and the full form.
    """
    by_key: dict[str, list[Construct]] = {}

    def add(key: str, c: Construct) -> None:
        by_key.setdefault(_normalize(key), []).append(c)

    for c in index:
        # Primary: full name.
        add(c.name, c)

        # `CALL X` → also index as `X` and `CALL X` verbatim.
        if c.name.upper().startswith("CALL "):
            tail = c.name[5:].strip()
            add(tail, c)

        # `%IF-%THEN/%ELSE` style compound macro headings: split on
        # `-` and `/` so each of `%if`, `%then`, `%else` resolves to the
        # same entry.
        if "-" in c.name or "/" in c.name:
            parts = re.split(r"[-/]", c.name)
            for p in parts:
                p = p.strip()
                if p:
                    add(p, c)

    return by_key


def pick_best(hits: list[Construct], file_key: str) -> Construct | None:
    """Given multiple index hits for the same name, pick the one whose
    category best matches the reference file's domain."""
    if not hits:
        return None
    if len(hits) == 1:
        return hits[0]

    priority = CATEGORY_PRIORITY.get(file_key, [])
    # Lower index in priority list = higher preference. Unknown
    # categories sort last.
    def score(c: Construct) -> int:
        try:
            return priority.index(c.category)
        except ValueError:
            return len(priority) + 1

    return sorted(hits, key=score)[0]


# Extract the bare name from a Quick Ref first-cell like "`%macro`" or
# "`%do` / `%end`" or "`do` / `end`". For compound rows we try each
# segment in order and accept the first that resolves; the display text
# (the original cell content) is used unchanged in the final markdown
# link so the reader sees the exact SAS syntax they typed.
NAME_CELL_RE = re.compile(r"`([^`]+)`")


def extract_names_from_cell(cell: str) -> list[str]:
    """Pull out backtick-wrapped names from a cell, in order.

    `` `%do` / `%end` `` → `['%do', '%end']`
    `` `call symputx` `` → `['call symputx']`
    """
    return NAME_CELL_RE.findall(cell)


def resolve_row(
    name_cell: str,
    lookup: dict[str, list[Construct]],
    file_key: str,
) -> Construct | None:
    """Try every backticked name in the cell; return the first hit."""
    for raw in extract_names_from_cell(name_cell):
        hits = lookup.get(_normalize(raw))
        if hits:
            best = pick_best(hits, file_key)
            if best is not None:
                return best
    return None


def process_file(
    path: Path,
    lookup: dict[str, list[Construct]],
) -> tuple[int, int, int]:
    """Rewrite `path` in place. Returns (filled, skipped_todo, total_todo).

    - `filled`: rows where `TODO (source pending)` was replaced by a link.
    - `skipped_todo`: rows whose name had no index entry — left as TODO.
    - `total_todo`: `filled + skipped_todo` (sanity check against table size).
    """
    original = path.read_text(encoding="utf-8")
    lines = original.splitlines(keepends=False)

    file_key = path.name
    filled = 0
    skipped = 0

    in_quick_ref = False
    out_lines: list[str] = []

    for idx, line in enumerate(lines):
        stripped = line.rstrip()

        # Start of Quick Ref table: the literal header row. Stay inside
        # until we hit a blank line or a non-pipe line.
        if stripped == QUICK_REF_HEADER:
            in_quick_ref = True
            out_lines.append(line)
            continue

        if in_quick_ref:
            if not stripped or not stripped.startswith("|"):
                in_quick_ref = False
                out_lines.append(line)
                continue

            # Skip the `|------|...` separator row.
            if re.match(r"^\|\s*[-:]+\s*(\|\s*[-:]+\s*)+\|?\s*$", stripped):
                out_lines.append(line)
                continue

            if TODO_MARKER not in line:
                out_lines.append(line)
                continue

            # Split into cells. Leading `|` produces an empty first
            # element and trailing `|` an empty last element — guard
            # both.
            cells = line.split("|")
            if len(cells) < 3:
                out_lines.append(line)
                continue

            # First "real" cell is cells[1], last is cells[-2] assuming
            # surrounding `|`s.
            name_cell = cells[1].strip()
            doc_cell_idx = len(cells) - 2
            doc_cell = cells[doc_cell_idx].strip()

            if doc_cell != TODO_MARKER:
                out_lines.append(line)
                continue

            hit = resolve_row(name_cell, lookup, file_key)
            if hit is None:
                skipped += 1
                out_lines.append(line)
                continue

            # Preserve leading/trailing whitespace inside the cell so the
            # pipe alignment is visually similar to the surrounding rows
            # (markdown renderers don't care, but git diffs do).
            link = f"[{name_cell}]({hit.canonical_url})"
            cells[doc_cell_idx] = f" {link} "
            new_line = "|".join(cells)
            out_lines.append(new_line)
            filled += 1
        else:
            out_lines.append(line)

    total_todo = filled + skipped

    # Preserve trailing newline convention of the original file.
    new_text = "\n".join(out_lines)
    if original.endswith("\n") and not new_text.endswith("\n"):
        new_text += "\n"

    if new_text != original:
        _atomic_write(path, new_text)

    return filled, skipped, total_todo


def _atomic_write(path: Path, text: str) -> None:
    """Write to a sibling tempfile, then rename — avoids partial writes."""
    dir_ = path.parent
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", dir=dir_)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp_name, path)
    except Exception:
        # If rename failed, clean up the temp file.
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def main() -> int:
    index = load_index()
    lookup = build_lookup(index)

    # Quick sanity probe to stderr — helps catch index regressions early.
    sample_keys = [
        "%macro",
        "%if",
        "set",
        "call symputx",
        "symget",
        "_n_",
    ]
    sys.stderr.write("make_quick_ref: index probe\n")
    for k in sample_keys:
        hits = lookup.get(_normalize(k), [])
        sys.stderr.write(
            f"  {k!r:<18} -> {len(hits)} hit(s)"
            f"{' | cats=' + ','.join(sorted({h.category for h in hits})) if hits else ''}\n"
        )

    targets = [
        REFERENCES_DIR / "macros.md",
        REFERENCES_DIR / "data-step.md",
    ]

    grand_filled = 0
    grand_total = 0
    for path in targets:
        filled, skipped, total = process_file(path, lookup)
        grand_filled += filled
        grand_total += total
        sys.stderr.write(
            f"{path.name}: {filled}/{total} filled ({skipped} not found)\n"
        )

    sys.stderr.write(
        f"Total filled: {grand_filled}/{grand_total}\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
