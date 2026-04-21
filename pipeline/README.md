# sas94-skill pipeline

Build-time tooling for the sas94-skill project. Not shipped to skill users.

## Purpose

Extract rules, idioms, and quick-reference data from MIT-licensed SAS ecosystem
sources (primarily `sasjs/lint` and `sasjs/core`) and hand-transcribed items
from `jphall663/GWU_data_mining`, producing JSON artifacts that seed the
skill's `references/*.md` files.

## Run commands

- `uv sync` — install pipeline dependencies (run once after cloning or after
  dependency changes).
- `uv run python extractors/<name>.py` — run a single extractor (added in
  Task 4).
- `uv run python make_coverage.py > ../docs/coverage-matrix.md` — regenerate
  coverage matrix (added in Task 6).
- `uv run python make_provenance.py > ../docs/rule-provenance.md` — regenerate
  provenance audit trail (added in Task 6).

## Cache policy

`cache/` holds local clones of upstream repositories (`cache/github/<repo>/`)
and any fetched HTTP responses (`cache/docs/<host>/`). All `cache/` paths are
gitignored at the repo root — reproducibility comes from SHAs recorded in
`sources.yaml`, not from committed snapshots.

Pipeline scripts should be deterministic: re-running an extractor against the
same cache must produce byte-identical JSON output. Sort keys, sort lists,
avoid time-dependent fields.

## Adding a new source

1. Append a `github`, `official_docs`, `lexjansen`, or `community` entry to
   the target block in `sources.yaml`.
2. If it's a GitHub source, record the pinned SHA (Task 3 covers the two
   initial sasjs clones; later additions pin their own).
3. If it's a new extractor, add a module under `extractors/` and document the
   JSON output schema in the module docstring.

## Skill-install exclusion

`pipeline/` is listed in the repo-root `.skillignore`. Users installing the
skill via `git clone` into `.claude/skills/` get only the skill content —
pipeline code, caches, and extractor outputs are not shipped.
