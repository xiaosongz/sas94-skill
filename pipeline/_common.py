"""Shared helpers for pipeline scripts.

Exposes repo-root / references-dir path constants and a minimal YAML
frontmatter parser so `make_provenance.py` and `make_coverage.py` do not
duplicate the same four lines.

Deliberately does NOT depend on PyYAML for the frontmatter reader — the
two top-level scripts only need a handful of keys (`title`,
`last_reviewed`, `scope`) and parse a known-format mini-dialect. Keeps the
two scripts runnable even if pipeline deps are not fully installed.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT: Path = Path(__file__).resolve().parent.parent
REFERENCES_DIR: Path = REPO_ROOT / "references"


def load_frontmatter(path: Path) -> dict[str, str]:
    """Parse a YAML-lite frontmatter block from a markdown file.

    Expects the file to start with a `---`-delimited block. Supports
    only `key: value` lines (no nested structures, no lists). Returns
    an empty dict if no frontmatter is present.

    This is intentionally NOT a full YAML parser — reference files in
    this repo use a flat `key: value` convention and we want zero
    dependency on PyYAML for the provenance / coverage scripts.
    """
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}
    block = text[4:end]
    out: dict[str, str] = {}
    for raw in block.splitlines():
        line = raw.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        # Strip surrounding single OR double quotes, but only if the
        # whole value is quoted. A quoted scope: line like 'foo "bar" baz'
        # stays intact.
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        out[key] = value
    return out


def body_after_frontmatter(path: Path) -> str:
    """Return the file body with the leading frontmatter block stripped."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return text
    end = text.find("\n---\n", 4)
    if end == -1:
        return text
    return text[end + len("\n---\n") :]
