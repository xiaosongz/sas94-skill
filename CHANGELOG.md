# Changelog

## v0.1.0-beta.1 — 2026-04-23

### Breaking

- **Reference layout restructured to atoms.** Every monolithic
  `references/<topic>.md` file has been split into a per-topic
  directory of per-concept atoms:
  `references/<topic>/<atom>.md` (~100-200 lines each, one to three
  Critical Rules per atom, CORRECT / WRONG pairs preserved).
  13 topic files became 12 topic directories + 75 atoms. The
  `sas-master-reference.md` aggregator was deleted — SKILL.md is
  now the authoritative router.
- **SKILL.md routing table rewritten.** Triggers map to specific
  atoms (e.g. `references/data-step/where-vs-if.md`) rather than
  whole topic files. Fallback: load `<topic>/_index.md` first when
  a trigger is ambiguous.
- **`Source:` URLs dropped from atoms.** A single SAS documentation
  base URL at the top of SKILL.md replaces ~200 inline citations.
  If an atom is insufficient, the agent is instructed to browse the
  base URL or do a general web search.
- **Motivation**: on a standard DATA-step + PROC MEANS + PROC GLM
  pipeline, an agent with access to the v0.0.1 monolithic layout
  consumed ~5× more tokens than an agent with no skill, because
  routing loaded 500-700-line topic files wholesale. The atom
  layout targets ≤20K agent-tokens on the same pipeline.

### Added

- New rules across reference atoms (carried over from v0.0.1 + added during refactor):
  - `data-step/where-vs-if.md` — WHERE (pre-PDV, compile-time) vs
    subsetting IF (post-PDV, execute-time); WHERE cannot see
    derived variables.
  - `base-procs/schema-utils.md` — PROC CONTENTS + PROC DATASETS;
    `KILL` destroys a library without confirmation.
  - `base-procs/file-io.md` — PROC IMPORT / EXPORT; default
    `GUESSINGROWS=1` for CSV silently truncates row-1-short
    columns; always pin `DBMS=`, `GETNAMES=`, `GUESSINGROWS=MAX`.
  - `base-procs/proc-compare.md` — PROC COMPARE default
    `METHOD=EXACT` is bit-strict; `CRITERION=0.00001` only
    applies under `METHOD=RELATIVE`/`PERCENT`; labels / formats /
    informats ignored by default — use
    `METHOD=EXACT CRITERION=0 LISTALL` for full coverage.
  - `macros/debugging.md` — `OPTIONS MPRINT / MLOGIC / SYMBOLGEN`,
    `OBS=0` dry run, `%PUT _USER_` / `%PUT _ALL_` symbol-table
    inspection.
  - `macros/include-vs-macro.md` — `%INCLUDE` is parse-time file
    inclusion without parameter scope; not a `%MACRO` substitute.
  - `formats-informats/date-formats.md` — `date9.` format + date
    literal row added to Quick Ref.

### Fixed

- Factually-wrong default claims in v0.0.1's PROC IMPORT +
  PROC COMPARE sections, corrected during the refactor.
- `case-length-when` WRONG-example comment clarified — it's a
  parse-time ERROR 22-322, not a silent failure (unique exception
  in the skill's WRONG-example convention).
- `.github/workflows/validate-sources.yml` path glob corrected
  from the stale pre-restructure `references/**/*.md` to the new
  `plugins/sas94/skills/sas94/references/**/*.md`.
- `.github/workflows/check-skill-load.yml` rewritten to check for
  path-qualified atom references (`references/<topic>/<atom>.md`)
  instead of bare filenames, and to require ≥10 topic directories
  and ≥40 atoms on disk.
- `pipeline/make_coverage.py` rewritten to walk the atom layout
  and report per-atom populated status.

### Docs

- `docs/CONTRIBUTING.md`, `docs/coverage-matrix.md`,
  `docs/design.md`, `docs/rule-provenance.md`, and `README.md`
  updated to describe the atom layout.
- `assets/analysis-template.sas` comment updated to point at the
  atom layout rather than the deleted aggregator.

### Known content gaps

- `base-procs/proc-compare.md` and `base-procs/proc-print.md`
  ship with a CORRECT example but no WRONG counterpart — the
  WRONG halves got re-homed to sibling atoms during the
  split. Follow-up: add topic-local WRONG examples.
- `functions-strings/case-and-compare.md` uses
  `## Critical behaviors` instead of the atom convention
  `## Critical Rules` + `### Rule N:`. Follow-up: rename for
  convention compliance.

## v0.0.1 — 2026-04-22

Initial release: 13 monolithic `references/*.md` topic files, plugin
marketplace layout under `.claude-plugin/` + `plugins/sas94/`.
