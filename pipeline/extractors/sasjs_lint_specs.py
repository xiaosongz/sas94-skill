"""Extract CORRECT/WRONG SAS snippets from sasjs-lint spec files.

For each `<rule>.spec.ts` under `src/rules/{line,file,path}/`:
  1. Find every `it('...', () => { ... })` block.
  2. Inside each block, capture named string constants
     (`const <varname> = <string-literal>`) — these hold the SAS snippet or
     path being tested.
  3. Classify the block CORRECT if its assertion is `toEqual([])` or
     `toHaveLength(0)`; WRONG if it expects a non-empty diagnostic array;
     UNKNOWN otherwise.
  4. Emit one example per (rule, it-block, captured-variable).

Run:
    uv run python pipeline/extractors/sasjs_lint_specs.py

Success criterion: every rule has >= 1 CORRECT and >= 1 WRONG snippet.
Rules that fall short get listed in `gaps[]` in the output JSON.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

PIPELINE_DIR = Path(__file__).resolve().parent.parent
SOURCES_YAML = PIPELINE_DIR / "sources.yaml"
LINT_RULES_DIR = PIPELINE_DIR / "cache" / "github" / "sasjs-lint" / "src" / "rules"
OUT_DIR = PIPELINE_DIR / "cache" / "extracted"
OUT_FILE = OUT_DIR / "sasjs_lint_examples.json"

SCOPES: tuple[str, ...] = ("line", "file", "path")

Classification = Literal["correct", "wrong", "unknown"]


class SasjsLintExample(BaseModel):
    rule_name: str
    scope: Literal["line", "file", "path"]
    classification: Classification
    variable_name: str  # e.g. "content", "line", "filePath"
    snippet: str
    snippet_hash: str  # short SHA-1 for dedup/sort tie-break
    spec_it_title: str  # the `it('...')` description
    spec_file_path: str  # relative to sasjs-lint repo root


class SasjsLintGap(BaseModel):
    rule_name: str
    reason: str


class SasjsLintExamplesOutput(BaseModel):
    examples: list[SasjsLintExample]
    gaps: list[SasjsLintGap] = Field(default_factory=list)
    source_sha: str | None
    source_repo: str = "https://github.com/sasjs/lint"
    example_count: int = 0
    rule_coverage: dict[str, dict[str, int]] = Field(default_factory=dict)


# --- TS parsing helpers -----------------------------------------------------


def _strip_single_quoted_or_double(src: str) -> str | None:
    """Un-escape a simple JS single- or double-quoted string (no template literals)."""
    if len(src) < 2:
        return None
    q = src[0]
    if q not in ("'", '"') or src[-1] != q:
        return None
    body = src[1:-1]
    # Handle common JS escapes: \n, \t, \r, \\, \', \"
    return (
        body.replace("\\\\", "\x00")  # temp placeholder for literal backslash
        .replace("\\n", "\n")
        .replace("\\r", "\r")
        .replace("\\t", "\t")
        .replace("\\'", "'")
        .replace('\\"', '"')
        .replace("\x00", "\\")
    )


def _extract_string_literal(source: str, start: int) -> tuple[str, int] | None:
    """Parse a JS string literal starting at `source[start]`.

    Supports single-quoted, double-quoted, and backtick template literals.
    For template literals, returns the raw inner text (no expression eval).
    Returns (decoded_string, end_index_after_closing_quote) or None.
    """
    if start >= len(source):
        return None
    q = source[start]
    if q not in ("'", '"', "`"):
        return None

    i = start + 1
    n = len(source)
    while i < n:
        ch = source[i]
        if ch == "\\" and i + 1 < n:
            # skip escape
            i += 2
            continue
        if q == "`" and ch == "$" and i + 1 < n and source[i + 1] == "{":
            # Skip over ${ ... } with brace tracking
            depth = 1
            i += 2
            while i < n and depth > 0:
                if source[i] == "{":
                    depth += 1
                elif source[i] == "}":
                    depth -= 1
                i += 1
            continue
        if ch == q:
            raw = source[start + 1 : i]
            if q == "`":
                # Template literal: keep as-is (no escape decoding; SAS snippets
                # don't rely on JS escapes in backtick strings)
                decoded = raw
            else:
                decoded_opt = _strip_single_quoted_or_double(source[start : i + 1])
                decoded = decoded_opt if decoded_opt is not None else raw
            return decoded, i + 1
        i += 1
    return None


def _find_matching_paren(source: str, start: int, open_ch: str, close_ch: str) -> int | None:
    """Return index AFTER matching close of a bracket-like pair starting at `source[start]`
    (source[start] must equal open_ch). Skips over string literals.
    Returns None on unbalanced input.
    """
    if start >= len(source) or source[start] != open_ch:
        return None
    depth = 0
    i = start
    n = len(source)
    while i < n:
        ch = source[i]
        if ch in ("'", '"', "`"):
            ret = _extract_string_literal(source, i)
            if ret is None:
                i += 1
                continue
            _, end = ret
            i = end
            continue
        if ch == open_ch:
            depth += 1
        elif ch == close_ch:
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return None


def _iter_it_blocks(source: str):
    """Yield (title, body_source, spec_offset) for each top-level `it(...)` call.

    `it` is matched as a bare identifier (with whitespace), not `describe.skip`.
    Nested `it`s inside nested describes are still captured — we walk the full
    file linearly.
    """
    # Match `it(` or `test(` — Jest lets you use either. Look for identifier
    # boundary. We allow either, since sasjs-lint uses `it`.
    pattern = re.compile(r"\b(it|test)\s*\(")
    pos = 0
    while True:
        m = pattern.search(source, pos)
        if not m:
            return
        open_paren = m.end() - 1
        end = _find_matching_paren(source, open_paren, "(", ")")
        if end is None:
            return
        inner = source[open_paren + 1 : end - 1]
        # First argument: string literal title
        stripped_offset = len(inner) - len(inner.lstrip())
        title_info = _extract_string_literal(inner, stripped_offset)
        title = title_info[0] if title_info else ""
        yield title, inner, m.start()
        pos = end


def _extract_content_vars(it_body: str) -> list[tuple[str, str]]:
    """Extract `const/let <name> = <string-literal>` inside an it-block body.

    Handles single-quoted, double-quoted, and backtick template strings.
    Returns list of (variable_name, string_content) in source order.
    """
    results: list[tuple[str, str]] = []
    pattern = re.compile(r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*")
    pos = 0
    while True:
        m = pattern.search(it_body, pos)
        if not m:
            break
        name = m.group(1)
        after_eq = m.end()
        # Skip whitespace
        while after_eq < len(it_body) and it_body[after_eq] in " \t\r\n":
            after_eq += 1
        if after_eq < len(it_body) and it_body[after_eq] in ("'", '"', "`"):
            ret = _extract_string_literal(it_body, after_eq)
            if ret is not None:
                text, end = ret
                results.append((name, text))
                pos = end
                continue
        pos = m.end()
    return results


_EMPTY_ASSERTIONS = (
    "toEqual([])",
    "toEqual( [] )",
    "toHaveLength(0)",
    "toHaveLength( 0 )",
    "toStrictEqual([])",
)


def _classify(it_body: str) -> Classification:
    """Classify a spec `it(...)` body as correct / wrong / unknown.

    Heuristic (WRONG wins on conflict — sasjs-lint specs often mix a setup
    `toEqual([])` with later `toContainEqual` assertions on violation cases):
      - WRONG when any of:
          * `toEqual([{...}])` / `toStrictEqual([{...}])` with object inside
          * `toContainEqual({...})` (always asserts a specific diagnostic)
          * `toEqual(<N>)` or `toHaveLength(<N>)` where N != 0 on a
            `diagnostics.length` expression
      - CORRECT when any `toEqual([])` / `toHaveLength(0)` / `toEqual(0)` on a
        `.length` expression, and no WRONG signal.
      - UNKNOWN otherwise.
    """
    normalized = re.sub(r"\s+", "", it_body)
    has_empty = any(
        re.sub(r"\s+", "", sig) in normalized for sig in _EMPTY_ASSERTIONS
    )
    has_nonempty_array = (
        "toEqual([{" in normalized or "toStrictEqual([{" in normalized
    )
    has_contain_equal = "toContainEqual({" in normalized
    # `expect(...length).toEqual(<n>)` or `.toBe(<n>)` where n != 0 -> WRONG.
    # Pattern: after normalize whitespace, look for `.length).toEqual(N)` with
    # N a non-zero integer literal.
    has_nonzero_length_equal = bool(
        re.search(r"\.length\)\.toEqual\((?!0\))\d+\)", normalized)
        or re.search(r"\.length\)\.toBe\((?!0\))\d+\)", normalized)
    )
    has_zero_length_equal = bool(
        re.search(r"\.length\)\.toEqual\(0\)", normalized)
        or re.search(r"\.length\)\.toBe\(0\)", normalized)
    )

    if has_nonempty_array or has_contain_equal or has_nonzero_length_equal:
        return "wrong"
    if has_empty or has_zero_length_equal:
        return "correct"
    return "unknown"


# --- Source SHA lookup ------------------------------------------------------


def _load_source_sha() -> str | None:
    if not SOURCES_YAML.exists():
        return None
    with SOURCES_YAML.open() as fh:
        manifest = yaml.safe_load(fh)
    for entry in manifest or []:
        for gh in entry.get("github") or []:
            if gh.get("repo", "").endswith("sasjs/lint"):
                sha = gh.get("sha")
                if sha:
                    return sha
    return None


# --- Core extraction --------------------------------------------------------


def _extract_spec_file(
    spec_path: Path, scope: str, rule_name: str
) -> list[SasjsLintExample]:
    source = spec_path.read_text(encoding="utf-8")
    examples: list[SasjsLintExample] = []
    lint_root = LINT_RULES_DIR.parent.parent  # -> .../sasjs-lint
    rel = spec_path.relative_to(lint_root).as_posix()

    for title, inner, _offset in _iter_it_blocks(source):
        classification = _classify(inner)
        for var_name, snippet in _extract_content_vars(inner):
            # Skip trivially short snippets (likely not SAS/path test input —
            # e.g. the enclosing `it(title, () => { ... })` arguments).
            if not snippet:
                continue
            snippet_hash = hashlib.sha1(snippet.encode("utf-8")).hexdigest()[:12]
            examples.append(
                SasjsLintExample(
                    rule_name=rule_name,
                    scope=scope,  # type: ignore[arg-type]
                    classification=classification,
                    variable_name=var_name,
                    snippet=snippet,
                    snippet_hash=snippet_hash,
                    spec_it_title=title,
                    spec_file_path=rel,
                )
            )
    return examples


def extract() -> SasjsLintExamplesOutput:
    if not LINT_RULES_DIR.exists():
        raise SystemExit(f"sasjs-lint rules dir not found: {LINT_RULES_DIR}")

    examples: list[SasjsLintExample] = []
    for scope in SCOPES:
        scope_dir = LINT_RULES_DIR / scope
        for spec_path in sorted(scope_dir.glob("*.spec.ts")):
            rule_name = spec_path.name.removesuffix(".spec.ts")
            examples.extend(_extract_spec_file(spec_path, scope, rule_name))

    # Sort deterministically: (rule_name, classification, snippet_hash)
    examples.sort(
        key=lambda e: (e.rule_name, e.classification, e.snippet_hash)
    )

    # Build per-rule coverage stats
    coverage: dict[str, dict[str, int]] = {}
    for e in examples:
        bucket = coverage.setdefault(
            e.rule_name, {"correct": 0, "wrong": 0, "unknown": 0}
        )
        bucket[e.classification] += 1

    # Identify rules that fail the >=1 CORRECT + >=1 WRONG criterion.
    # We source the rule list from the extractor output (if present) or from
    # the rules dir directly, to ensure every rule is audited even if its
    # spec file yielded no examples.
    all_rule_names: set[str] = set()
    for scope in SCOPES:
        scope_dir = LINT_RULES_DIR / scope
        for ts_path in scope_dir.glob("*.ts"):
            if ts_path.name == "index.ts" or ts_path.name.endswith(".spec.ts"):
                continue
            all_rule_names.add(ts_path.stem)

    gaps: list[SasjsLintGap] = []
    for rule_name in sorted(all_rule_names):
        cov = coverage.get(rule_name, {"correct": 0, "wrong": 0, "unknown": 0})
        if cov["correct"] == 0 and cov["wrong"] == 0 and cov["unknown"] == 0:
            gaps.append(
                SasjsLintGap(
                    rule_name=rule_name,
                    reason="no examples extracted from spec file",
                )
            )
            continue
        missing = []
        if cov["correct"] == 0:
            missing.append("correct")
        if cov["wrong"] == 0:
            missing.append("wrong")
        if missing:
            gaps.append(
                SasjsLintGap(
                    rule_name=rule_name,
                    reason=f"missing classification(s): {', '.join(missing)}",
                )
            )

    return SasjsLintExamplesOutput(
        examples=examples,
        gaps=gaps,
        source_sha=_load_source_sha(),
        example_count=len(examples),
        rule_coverage=coverage,
    )


# --- CLI --------------------------------------------------------------------


def main() -> int:
    out = extract()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = out.model_dump()
    OUT_FILE.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    # Reporting
    print(f"wrote {OUT_FILE} ({out.example_count} examples)")
    print(f"  rule coverage (correct/wrong/unknown):")
    for rule_name in sorted(out.rule_coverage):
        cov = out.rule_coverage[rule_name]
        print(
            f"    {rule_name}: "
            f"{cov['correct']}/{cov['wrong']}/{cov['unknown']}"
        )
    if out.gaps:
        print(f"  gaps ({len(out.gaps)}):")
        for gap in out.gaps:
            print(f"    {gap.rule_name}: {gap.reason}")
    else:
        print("  no gaps — all rules have >=1 correct + >=1 wrong example")

    # Assertion per Task 4 success criterion.
    # We WARN (non-fatal) if any gap exists — the gap list is recorded in the
    # JSON output so downstream stages can triage. The Task 4 plan explicitly
    # allows recording gaps rather than hard-failing.
    return 0


if __name__ == "__main__":
    sys.exit(main())
