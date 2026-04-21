"""Extract Doxygen headers from sasjs-core/base/*.sas files.

For each `base/*.sas`:
  1. Read the first 40 lines (per task plan).
  2. Locate the Doxygen block `/** ... **/` at the top of the file.
  3. Extract @brief, @details, @param [dir] name= (default) desc, @returns,
     @version, @author.
  4. Parse the `%macro <name>(...)` line after the header to get macro_name.

Run:
    uv run python pipeline/extractors/sasjs_core_doxygen.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

PIPELINE_DIR = Path(__file__).resolve().parent.parent
SOURCES_YAML = PIPELINE_DIR / "sources.yaml"
BASE_DIR = PIPELINE_DIR / "cache" / "github" / "sasjs-core" / "base"
OUT_DIR = PIPELINE_DIR / "cache" / "extracted"
OUT_FILE = OUT_DIR / "sasjs_core_doxygen.json"

HEADER_LINE_LIMIT = 40

ParamDirection = Literal["in", "out", "in,out"]


class DoxygenParam(BaseModel):
    name: str
    direction: str | None  # "in" | "out" | "in,out" | None
    default: str | None
    description: str | None


class DoxygenMacro(BaseModel):
    macro_name: str | None
    file: str  # basename, e.g. "mf_abort.sas"
    brief: str | None
    details: str | None
    params: list[DoxygenParam] = Field(default_factory=list)
    returns: str | None
    version: str | None
    author: str | None


class SasjsCoreDoxygenOutput(BaseModel):
    macros: list[DoxygenMacro]
    source_sha: str | None
    source_repo: str = "https://github.com/sasjs/core"
    source_path: str = "base/"
    macro_count: int = Field(..., description="len(macros)")
    brief_coverage_pct: float = Field(
        ..., description="pct of macros with non-empty brief"
    )


# --- Regex helpers ----------------------------------------------------------


_HEADER_RE = re.compile(r"/\*\*(.*?)\*\*/", re.DOTALL)
# Param prefix: `@param [dir] name=` — direction + default handled separately
# so we can do balanced-paren matching on the default parenthetical.
_PARAM_PREFIX_RE = re.compile(
    r"@param\s+"
    r"(?:\[(?P<dir>in,\s*out|in|out)\]\s+)?"
    r"(?P<name>\w+)(?P<has_eq>=?)\s*",
)
_MACRO_DEF_RE = re.compile(r"%macro\s+([A-Za-z_][\w]*)", re.IGNORECASE)


def _extract_balanced_parens(text: str, start: int) -> tuple[str, int] | None:
    """If text[start] == '(', return (inner_text, end_index_after_close).

    Balanced-paren aware so defaults like `(%str(1=1))` are captured in full.
    Returns None if no opening paren at start, or unbalanced.
    """
    if start >= len(text) or text[start] != "(":
        return None
    depth = 0
    i = start
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return text[start + 1 : i], i + 1
        i += 1
    return None


def _load_source_sha() -> str | None:
    if not SOURCES_YAML.exists():
        return None
    with SOURCES_YAML.open() as fh:
        manifest = yaml.safe_load(fh)
    for entry in manifest or []:
        for gh in entry.get("github") or []:
            if gh.get("repo", "").endswith("sasjs/core"):
                sha = gh.get("sha")
                if sha:
                    return sha
    return None


def _strip_leading_star_or_space(line: str) -> str:
    """Remove leading whitespace + optional leading `*` continuation marker.

    Most Doxygen block bodies don't use `*` prefixes in this codebase, but we
    handle it defensively.
    """
    return re.sub(r"^[\s*]+", "", line).rstrip()


def _normalize_field(text: str) -> str:
    """Collapse consecutive spaces/newlines in field text, strip."""
    return re.sub(r"\s+", " ", text).strip()


def _extract_header_lines(body: str) -> list[str]:
    """Turn the Doxygen block body (inside /** ... **/) into clean lines.

    Drops blank-only lines entirely; keeps logical line order for later
    continuation-line joining.
    """
    lines: list[str] = []
    for raw in body.splitlines():
        stripped = _strip_leading_star_or_space(raw)
        lines.append(stripped)
    return lines


def _extract_tag_block(
    lines: list[str], tag: str
) -> str | None:
    """Join lines belonging to `@<tag>` up to the next `@<tag2>` or blank line.

    Returns None if no `@<tag>` line found. Multi-line continuations are
    joined with a single space.
    """
    tag_prefix = f"@{tag}"
    collected: list[str] = []
    found = False
    for ln in lines:
        if ln.startswith(tag_prefix):
            # Start (or re-start on duplicate tag — we take the first occurrence)
            if found:
                break
            found = True
            # Strip the tag itself (handle "@brief foo" and bare "@brief")
            rest = ln[len(tag_prefix) :].lstrip()
            if rest:
                collected.append(rest)
            continue
        if not found:
            continue
        # Continuation: blank line or new tag ends the block
        if ln == "":
            break
        if ln.startswith("@"):
            break
        # Also stop on `<h4>` section headers, `@li` list markers below.
        if ln.startswith("<h") or ln.startswith("@li"):
            break
        collected.append(ln)

    if not found:
        return None
    joined = _normalize_field(" ".join(collected))
    return joined or None


def _extract_params(lines: list[str]) -> list[DoxygenParam]:
    """Walk header lines, gather @param entries (supporting multi-line desc).

    Uses balanced-paren matching on the default parenthetical so defaults like
    `(%str(1=1))` are captured in full rather than truncated at the first `)`.
    """
    params: list[DoxygenParam] = []
    i = 0
    n = len(lines)
    while i < n:
        ln = lines[i]
        if ln.startswith("@param"):
            # Greedy: collect continuation lines until next @ or blank or <h> or @li
            block_parts = [ln]
            j = i + 1
            while j < n:
                nxt = lines[j]
                if (
                    nxt == ""
                    or nxt.startswith("@")
                    or nxt.startswith("<h")
                    or nxt.startswith("@li")
                ):
                    break
                block_parts.append(nxt)
                j += 1
            block = " ".join(block_parts)

            m = _PARAM_PREFIX_RE.match(block)
            if m:
                direction = m.group("dir")
                if direction:
                    direction = re.sub(r"\s+", "", direction)
                name = m.group("name")
                cursor = m.end()
                default: str | None = None
                # Skip whitespace, then try balanced paren match for default
                while cursor < len(block) and block[cursor] == " ":
                    cursor += 1
                if cursor < len(block) and block[cursor] == "(":
                    ret = _extract_balanced_parens(block, cursor)
                    if ret is not None:
                        default, cursor = ret
                desc_raw = block[cursor:].strip()
                desc = _normalize_field(desc_raw) or None
                params.append(
                    DoxygenParam(
                        name=name,
                        direction=direction,
                        default=default,
                        description=desc,
                    )
                )
            i = j
            continue
        i += 1
    return params


def _extract_macro_name(full_source: str, header_end: int) -> str | None:
    """Find the first `%macro <name>(` after the header block close."""
    m = _MACRO_DEF_RE.search(full_source, header_end)
    if m:
        return m.group(1)
    return None


def _extract_one_file(sas_path: Path) -> DoxygenMacro:
    """Parse Doxygen header + macro name from a .sas file.

    Per task plan, the header opener `/**` must be in the first
    HEADER_LINE_LIMIT (40) lines — this bounds how far we scan for a header
    start. Once found, we read forward in the full file for the closing `**/`,
    since several sasjs-core headers (e.g. mp_abort.sas) are longer than 40
    lines.
    """
    full = sas_path.read_text(encoding="utf-8", errors="replace")
    head_lines = full.splitlines()[:HEADER_LINE_LIMIT]
    head_region = "\n".join(head_lines)

    brief = details = returns = version = author = None
    params: list[DoxygenParam] = []
    header_end_offset = 0

    # Look for `/**` opener within the first N lines.
    opener_match = re.search(r"/\*\*", head_region)
    header_match = None
    if opener_match:
        # Convert the head-region offset to a full-source offset. Since
        # head_region is a strict prefix of full (joined with \n), the offsets
        # match up to the length of head_region.
        opener_abs = opener_match.start()
        header_match = _HEADER_RE.search(full, opener_abs)

    if header_match:
        body = header_match.group(1)
        lines = _extract_header_lines(body)
        brief = _extract_tag_block(lines, "brief")
        details = _extract_tag_block(lines, "details")
        # Support @returns or @return (some files use singular)
        returns = _extract_tag_block(lines, "returns") or _extract_tag_block(
            lines, "return"
        )
        version = _extract_tag_block(lines, "version")
        author = _extract_tag_block(lines, "author")
        params = _extract_params(lines)
        header_end_offset = header_match.end()

    macro_name = _extract_macro_name(full, header_end_offset)

    return DoxygenMacro(
        macro_name=macro_name,
        file=sas_path.name,
        brief=brief,
        details=details,
        params=params,
        returns=returns,
        version=version,
        author=author,
    )


def extract() -> SasjsCoreDoxygenOutput:
    if not BASE_DIR.exists():
        raise SystemExit(f"sasjs-core base/ dir not found: {BASE_DIR}")

    macros: list[DoxygenMacro] = []
    for sas_path in sorted(BASE_DIR.glob("*.sas")):
        macros.append(_extract_one_file(sas_path))

    # Deterministic ordering: sort by file basename (already sorted from glob,
    # but be explicit).
    macros.sort(key=lambda m: m.file)

    non_empty_brief = sum(1 for m in macros if m.brief)
    total = len(macros)
    pct = round(100.0 * non_empty_brief / total, 2) if total else 0.0

    return SasjsCoreDoxygenOutput(
        macros=macros,
        source_sha=_load_source_sha(),
        macro_count=total,
        brief_coverage_pct=pct,
    )


def main() -> int:
    out = extract()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = out.model_dump()
    OUT_FILE.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        f"wrote {OUT_FILE} ({out.macro_count} macros, "
        f"brief coverage {out.brief_coverage_pct}%)"
    )

    # Sanity: task plan requires >=95% brief coverage.
    missing_brief = [m.file for m in out.macros if not m.brief]
    if missing_brief:
        print(f"  {len(missing_brief)} files missing @brief:")
        for f in missing_brief[:10]:
            print(f"    {f}")
        if len(missing_brief) > 10:
            print(f"    ... and {len(missing_brief) - 10} more")

    assert out.brief_coverage_pct >= 95.0, (
        f"brief coverage {out.brief_coverage_pct}% below 95% threshold; "
        f"{len(missing_brief)} files missing @brief"
    )

    # Spot-check: sample 10 macros, print brief + file so the operator can
    # eyeball-verify against the source. (Task step 7.)
    print("  spot-check sample (first 10 by filename):")
    for m in out.macros[:10]:
        print(f"    {m.file}: {m.brief!r}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
