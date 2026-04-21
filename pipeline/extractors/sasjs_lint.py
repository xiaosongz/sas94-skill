"""Extract sasjs-lint rule metadata from src/rules/{line,file,path}/*.ts.

Run from repo root or pipeline dir:

    uv run python pipeline/extractors/sasjs_lint.py

Emits pipeline/cache/extracted/sasjs_lint_rules.json.
Output is deterministic: rules sorted by (scope, name), JSON with sort_keys.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

# Repo-relative paths (resolved against PIPELINE_DIR = .../sas94-skill/pipeline)
PIPELINE_DIR = Path(__file__).resolve().parent.parent
SOURCES_YAML = PIPELINE_DIR / "sources.yaml"
LINT_RULES_DIR = PIPELINE_DIR / "cache" / "github" / "sasjs-lint" / "src" / "rules"
OUT_DIR = PIPELINE_DIR / "cache" / "extracted"
OUT_FILE = OUT_DIR / "sasjs_lint_rules.json"

SCOPES: tuple[str, ...] = ("line", "file", "path")


class SasjsLintRule(BaseModel):
    name: str
    scope: Literal["line", "file", "path"]
    description: str | None
    severity: str | None
    message_template: str | None
    file_path: str  # relative path from sasjs-lint repo root
    has_fix: bool


class SasjsLintRulesOutput(BaseModel):
    rules: list[SasjsLintRule]
    source_sha: str | None
    source_repo: str = "https://github.com/sasjs/lint"
    rule_count: int = Field(..., description="len(rules)")


# --- Regex helpers ----------------------------------------------------------


def _extract_string_const(source: str, const_name: str) -> str | None:
    """Extract a top-level `const <name> = '...'` or `"..."` literal.

    Only matches single-line single/double quoted strings — sufficient for
    sasjs-lint's `name`, `description`, `message` declarations.
    """
    pattern = rf"^\s*const\s+{re.escape(const_name)}\s*=\s*(['\"])(.*?)\1"
    m = re.search(pattern, source, re.MULTILINE)
    if m is None:
        return None
    return m.group(2)


def _detect_has_fix(source: str) -> bool:
    """Detect if the rule module exports a `fix` property or defines `const fix`.

    Conservative: match either `const fix` declaration or a `fix,` / `fix:` line
    inside the exported rule object.
    """
    if re.search(r"^\s*const\s+fix\s*=", source, re.MULTILINE):
        return True
    # `fix,` inside an object literal (same-shorthand), or `fix: ...` explicit.
    if re.search(r"^\s*fix\s*[,:]", source, re.MULTILINE):
        return True
    return False


def _detect_severity(source: str) -> str | None:
    """Extract the default severity used by the rule.

    sasjs-lint rules set severity via:

        const severity = config?.severityLevel[name] || Severity.Warning

    We capture the `Severity.X` fallback — that is the effective default.
    Returns a string like "Warning" / "Error" / "Info", or None if not matched.
    """
    m = re.search(
        r"config\??\.severityLevel\[\s*name\s*\]\s*\|\|\s*Severity\.(Info|Warning|Error)",
        source,
    )
    if m:
        return m.group(1)
    # Fallback: bare Severity.X reference (e.g., if rule hard-codes severity)
    m = re.search(r"severity\s*:\s*Severity\.(Info|Warning|Error)", source)
    if m:
        return m.group(1)
    return None


def _load_source_sha() -> str | None:
    """Pull the sasjs-lint commit SHA from sources.yaml manifest."""
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


def _extract_rule_file(ts_path: Path, scope: str) -> SasjsLintRule:
    source = ts_path.read_text(encoding="utf-8")
    name = _extract_string_const(source, "name") or ts_path.stem
    description = _extract_string_const(source, "description")
    message = _extract_string_const(source, "message")
    severity = _detect_severity(source)
    has_fix = _detect_has_fix(source)

    # Build file_path relative to sasjs-lint repo root
    # LINT_RULES_DIR = .../sasjs-lint/src/rules, so .parent.parent = .../sasjs-lint
    lint_root = LINT_RULES_DIR.parent.parent
    rel = ts_path.relative_to(lint_root).as_posix()

    return SasjsLintRule(
        name=name,
        scope=scope,  # type: ignore[arg-type]
        description=description,
        severity=severity,
        message_template=message,
        file_path=rel,
        has_fix=has_fix,
    )


def extract() -> SasjsLintRulesOutput:
    if not LINT_RULES_DIR.exists():
        raise SystemExit(
            f"sasjs-lint rules dir not found: {LINT_RULES_DIR}\n"
            "Did you run the clone step in pipeline/sources.yaml?"
        )

    rules: list[SasjsLintRule] = []
    for scope in SCOPES:
        scope_dir = LINT_RULES_DIR / scope
        for ts_path in sorted(scope_dir.glob("*.ts")):
            # Skip index.ts and *.spec.ts
            if ts_path.name == "index.ts":
                continue
            if ts_path.name.endswith(".spec.ts"):
                continue
            rules.append(_extract_rule_file(ts_path, scope))

    # Sort deterministically by (scope_priority, name) — scope priority matches SCOPES
    scope_order = {s: i for i, s in enumerate(SCOPES)}
    rules.sort(key=lambda r: (scope_order[r.scope], r.name))

    return SasjsLintRulesOutput(
        rules=rules,
        source_sha=_load_source_sha(),
        rule_count=len(rules),
    )


# --- CLI --------------------------------------------------------------------


def main() -> int:
    out = extract()

    # Assertions (per Task 4 success criterion)
    expected = 15
    assert out.rule_count == expected, (
        f"expected {expected} sasjs-lint rules, got {out.rule_count}: "
        f"{[r.name for r in out.rules]}"
    )
    # Every rule must have at least a name and file_path
    for r in out.rules:
        assert r.name, f"rule missing name: {r}"
        assert r.file_path, f"rule missing file_path: {r}"

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = out.model_dump()
    OUT_FILE.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {OUT_FILE} ({out.rule_count} rules)")
    # Quick scope breakdown for eyeball validation
    from collections import Counter

    counts = Counter(r.scope for r in out.rules)
    print(f"  scope breakdown: {dict(counts)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
