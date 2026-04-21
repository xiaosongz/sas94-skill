"""Verify every `### Rule N:` and `### Idiom:` heading in `references/*.md`
has a `Source: <url>` line within the next 5 lines.

Called two ways:

1. Pre-commit hook — receives staged filenames as CLI args; checks only
   those files (fast path).
2. CI / manual — no args → walks every `references/*.md`.

Exit 0 when all headings carry a Source URL within the 5-line window;
exit 1 otherwise, printing `file:line: <diagnostic>` to stderr for each
offending heading (GitHub Actions and most editors parse this format).

Intentionally stdlib-only — this hook must run before `uv sync`, so we
cannot depend on PyYAML or httpx.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# `### Rule N: Title...` or `### Idiom: Title...`. We capture the heading
# text only for diagnostics — the hook does not care about rule numbers.
HEADING_RE = re.compile(r"^###\s+(Rule(?:\s+\d+)?|Idiom):\s*(.+?)\s*$")

# A Source line looks like `Source: https://... [optional trailing note]`.
# The URL itself must be http(s); anything else is rejected as a stub.
SOURCE_RE = re.compile(r"^Source:\s+https?://\S+")

# Look-ahead window (lines after the heading) for the Source line.
WINDOW = 5

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
REFERENCES_DIR = REPO_ROOT / "references"


def scan_file(path: Path) -> list[str]:
    """Return a list of violation strings for one file.

    Each violation is `relpath:lineno: missing Source URL after heading: <text>`.
    Empty list means the file is clean.
    """
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return [f"{path}: could not read file: {exc}"]

    violations: list[str] = []
    for idx, line in enumerate(lines):
        match = HEADING_RE.match(line)
        if not match:
            continue
        heading_kind = match.group(1)
        heading_text = match.group(2).strip()

        end = min(idx + 1 + WINDOW, len(lines))
        found = any(SOURCE_RE.match(lines[j]) for j in range(idx + 1, end))
        if not found:
            # 1-based line number for editor / GH Actions annotation
            # conventions. Heading text may contain SAS operators — quote
            # it so diagnostics are unambiguous.
            try:
                rel = path.relative_to(REPO_ROOT)
            except ValueError:
                rel = path
            violations.append(
                f"{rel}:{idx + 1}: missing Source URL within {WINDOW} lines "
                f"after heading: ### {heading_kind}: {heading_text!r}"
            )
    return violations


def resolve_targets(files: list[str]) -> list[Path]:
    """Filter CLI args down to `references/*.md` files.

    When `files` is empty, fall back to walking the full directory — this
    is the CI / manual path.
    """
    if not files:
        return sorted(REFERENCES_DIR.glob("*.md"))

    targets: list[Path] = []
    for name in files:
        p = Path(name).resolve()
        # Only check files under references/. Pre-commit may pass any
        # staged file — skip anything that isn't a references/*.md.
        try:
            rel = p.relative_to(REFERENCES_DIR)
        except ValueError:
            continue
        if rel.suffix == ".md" and len(rel.parts) == 1:
            targets.append(p)
    return targets


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify every Rule/Idiom heading in references/*.md "
        "has a Source URL within 5 lines.",
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Files to check (pre-commit passes staged filenames). "
        "Empty → walk references/*.md.",
    )
    args = parser.parse_args(argv)

    targets = resolve_targets(args.files)
    if not targets:
        # Nothing to check (e.g. pre-commit staged only non-reference files).
        # Return 0 so the hook doesn't block unrelated commits.
        return 0

    all_violations: list[str] = []
    for path in targets:
        all_violations.extend(scan_file(path))

    if all_violations:
        sys.stderr.write(
            "check-source-urls: found missing Source URLs:\n"
        )
        for v in all_violations:
            sys.stderr.write(f"  {v}\n")
        sys.stderr.write(
            "\nAdd a 'Source: <URL>' line within 5 lines after each heading.\n"
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
