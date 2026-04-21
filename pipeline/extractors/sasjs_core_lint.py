"""Extract sasjs-core's `.sasjslint` config into a structured JSON object.

Source: `pipeline/cache/github/sasjs-core/.sasjslint` (JSON).

Run:
    uv run python pipeline/extractors/sasjs_core_lint.py

The source file has 13 keys (plan text said 8, but the on-disk file is the
source of truth). Extractor emits all keys faithfully.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

PIPELINE_DIR = Path(__file__).resolve().parent.parent
SOURCES_YAML = PIPELINE_DIR / "sources.yaml"
CORE_DIR = PIPELINE_DIR / "cache" / "github" / "sasjs-core"
CONFIG_FILE = CORE_DIR / ".sasjslint"
OUT_DIR = PIPELINE_DIR / "cache" / "extracted"
OUT_FILE = OUT_DIR / "sasjs_core_lint_config.json"


class SasjsCoreLintConfigOutput(BaseModel):
    config: dict[str, Any]
    rule_count: int = Field(..., description="len(config.keys())")
    source_sha: str | None
    source_repo: str = "https://github.com/sasjs/core"
    source_path: str = ".sasjslint"


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


def extract() -> SasjsCoreLintConfigOutput:
    if not CONFIG_FILE.exists():
        raise SystemExit(f"sasjs-core .sasjslint not found: {CONFIG_FILE}")

    raw = CONFIG_FILE.read_text(encoding="utf-8")
    config = json.loads(raw)
    if not isinstance(config, dict):
        raise SystemExit(
            f".sasjslint root must be an object, got {type(config).__name__}"
        )

    return SasjsCoreLintConfigOutput(
        config=config,
        rule_count=len(config),
        source_sha=_load_source_sha(),
    )


def main() -> int:
    out = extract()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = out.model_dump()
    OUT_FILE.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {OUT_FILE} ({out.rule_count} config keys)")
    for k in sorted(out.config):
        print(f"  {k}: {out.config[k]!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
