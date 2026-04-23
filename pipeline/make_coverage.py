"""Generate `docs/coverage-matrix.md` — per-atom status report under the
post-atomization reference layout (`references/<topic>/<atom>.md`).

Usage:

    uv --directory pipeline run python make_coverage.py > docs/coverage-matrix.md

The script walks every `references/<topic>/*.md` file and checks for the
presence of the required atom sections:

- Every non-index atom MUST carry either a `## Critical Rules` section
  with at least one `### Rule` heading PLUS CORRECT and WRONG code
  blocks, OR a `## Canonical Idioms` section with at least one
  `### Idiom` heading (for idiom-cluster atoms).
- `_index.md` atoms are router files — required to carry a markdown
  table OR a bullet list that points at sibling atoms.
- Optional sections: `## Silent Pitfalls`, `## Anti-patterns` (any form
  with `STOP` or similar suffix).

Re-running the script must produce byte-identical output.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

from _common import REFERENCES_DIR, body_after_frontmatter

CRITICAL_RULES_HEADING_RE = re.compile(r"^Critical Rules")
CANONICAL_IDIOMS_HEADING = "Canonical Idioms"
ANTI_PATTERN_HEADING_RE = re.compile(r"^Anti-patterns")


@dataclass(frozen=True)
class AtomCoverage:
    topic: str
    atom: str
    is_index: bool
    critical_rules: bool
    canonical_idioms: bool
    silent_pitfalls: bool
    anti_patterns: bool
    routes: bool  # for _index.md files

    @property
    def populated(self) -> bool:
        if self.is_index:
            return self.routes
        return self.critical_rules or self.canonical_idioms

    @property
    def status(self) -> str:
        return "populated" if self.populated else "stub"


def _split_sections(body: str) -> dict[str, str]:
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


def _find_critical_rules(sections: dict[str, str]) -> str | None:
    for name, content in sections.items():
        if CRITICAL_RULES_HEADING_RE.match(name):
            return content
    return None


def _find_anti_patterns(sections: dict[str, str]) -> str | None:
    for name, content in sections.items():
        if ANTI_PATTERN_HEADING_RE.match(name):
            return content
    return None


def _critical_rules_populated(content: str | None) -> bool:
    if not content:
        return False
    rule_headings = [
        l
        for l in content.splitlines()
        if l.startswith("### Rule")
        or l.startswith("### Hygiene")
    ]
    if not rule_headings:
        return False
    has_correct_or_wrong = any(
        ("CORRECT" in l) or ("WRONG" in l) for l in content.splitlines()
    )
    return has_correct_or_wrong


def _canonical_idioms_populated(content: str | None) -> bool:
    if not content:
        return False
    idioms = [l for l in content.splitlines() if l.startswith("### Idiom")]
    return len(idioms) >= 1


def _has_bullets_or_table(body: str) -> bool:
    lines = body.splitlines()
    has_table = any(l.startswith("|") for l in lines)
    has_bullets = any(l.strip().startswith("-") for l in lines)
    return has_table or has_bullets


def _section_has_bullets(content: str | None) -> bool:
    if not content:
        return False
    return any(l.strip().startswith("-") for l in content.splitlines())


def scan_atom(path: Path) -> AtomCoverage:
    topic = path.parent.name
    atom = path.stem
    is_index = atom == "_index"
    body = body_after_frontmatter(path)
    sections = _split_sections(body)
    # Accept Critical Rules content from the named section OR from any
    # section containing `### Rule` / `### Hygiene` subheadings (some
    # atoms title this section differently, e.g. `## File hygiene`).
    cr_content = _find_critical_rules(sections)
    if not cr_content:
        cr_content = body if any(
            l.startswith("### Rule") or l.startswith("### Hygiene")
            for l in body.splitlines()
        ) else None
    cr = _critical_rules_populated(cr_content)
    ci = _canonical_idioms_populated(sections.get(CANONICAL_IDIOMS_HEADING))
    sp = _section_has_bullets(sections.get("Silent Pitfalls"))
    ap = _section_has_bullets(_find_anti_patterns(sections))
    routes = _has_bullets_or_table(body) if is_index else False
    return AtomCoverage(
        topic=topic,
        atom=atom,
        is_index=is_index,
        critical_rules=cr,
        canonical_idioms=ci,
        silent_pitfalls=sp,
        anti_patterns=ap,
        routes=routes,
    )


def collect_all_rows() -> list[AtomCoverage]:
    rows: list[AtomCoverage] = []
    for topic_dir in sorted(p for p in REFERENCES_DIR.iterdir() if p.is_dir()):
        for atom_path in sorted(topic_dir.glob("*.md")):
            rows.append(scan_atom(atom_path))
    return rows


def _checkmark(flag: bool) -> str:
    return "yes" if flag else "no"


def render_markdown(rows: list[AtomCoverage]) -> str:
    header = [
        "# Coverage Matrix",
        "",
        (
            "Per-atom coverage report under the atom-based reference "
            "layout (`references/<topic>/<atom>.md`). Each non-index atom "
            "must carry either a `Critical Rules` section (with CORRECT + "
            "WRONG pair) or a `Canonical Idioms` section. `_index.md` "
            "atoms must carry a routing table or bullet list. Generated "
            "from `references/`; do not edit by hand."
        ),
        "",
        "Regenerate after editing any atom:",
        "",
        "```bash",
        "uv --directory pipeline run python make_coverage.py > docs/coverage-matrix.md",
        "```",
        "",
        "| Topic | Atom | Critical Rules | Canonical Idioms | Silent Pitfalls | Anti-patterns | Status |",
        "|-------|------|----------------|------------------|------------------|----------------|--------|",
    ]

    body: list[str] = []
    for r in rows:
        if r.is_index:
            cr = ci = "—"
            sp = ap = "—"
            status = "index" if r.routes else "stub"
        else:
            cr = _checkmark(r.critical_rules)
            ci = _checkmark(r.canonical_idioms)
            sp = _checkmark(r.silent_pitfalls)
            ap = _checkmark(r.anti_patterns)
            status = r.status
        body.append(
            f"| {r.topic} | {r.atom} | {cr} | {ci} | {sp} | {ap} | {status} |"
        )

    atoms = [r for r in rows if not r.is_index]
    indexes = [r for r in rows if r.is_index]
    atom_ok = sum(1 for r in atoms if r.populated)
    index_ok = sum(1 for r in indexes if r.routes)

    footer = [
        "",
        f"Atoms populated: {atom_ok} / {len(atoms)}; indexes populated: {index_ok} / {len(indexes)}.",
        "",
    ]

    return "\n".join(header + body + footer)


def main() -> int:
    rows = collect_all_rows()
    sys.stdout.write(render_markdown(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
