"""Shared helpers for pipeline scripts.

Exposes repo-root / references-dir path constants and a YAML frontmatter
parser so `make_provenance.py` and `make_coverage.py` do not duplicate
the same few lines.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO_ROOT: Path = Path(__file__).resolve().parent.parent
REFERENCES_DIR: Path = REPO_ROOT / "references"


def load_frontmatter(path: Path) -> dict:
    """Parse YAML frontmatter block at the top of a markdown file.

    Returns empty dict if no '---\\n...\\n---' block is present at the top.
    Raises yaml.YAMLError if the block is present but malformed.
    """
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        return {}
    data = yaml.safe_load(m.group(1))
    return data if isinstance(data, dict) else {}


def body_after_frontmatter(path: Path) -> str:
    """Return the file body with the leading frontmatter block stripped."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return text
    end = text.find("\n---\n", 4)
    if end == -1:
        return text
    return text[end + len("\n---\n") :]
