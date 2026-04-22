# sas94-skill

A [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skill for
writing, reviewing, and debugging SAS 9.4 code with AI assistance.

SAS 9.4 is the daily driver for biostatisticians, health-services
researchers, and pharma/claims analysts, yet SAS is underrepresented in LLM
training corpora. This skill distills rules and idioms from MIT-licensed
sources (`sasjs/lint`, `sasjs/core`) plus hand-transcribed SAS-programmer
pitfalls (GWU data-mining curriculum), and routes Claude Code to
topic-specific reference files on demand.

**Status:** `v0.0.1` pre-release. All 13 reference files are 100%
populated across both REQUIRED sections (Overview, Critical Rules,
Canonical Idioms, Function/Statement Quick Ref, See Also) and OPTIONAL
sections (Silent Pitfalls, Anti-patterns). See
[`docs/coverage-matrix.md`](docs/coverage-matrix.md) for per-file
status.

## What This Skill Does

When activated, Claude Code can:

- **Translate** study descriptions into idiomatic SAS 9.4 (DATA step, PROC
  SQL, macros, PROC FREQ/MEANS/LOGISTIC, hash tables, ODS)
- **Catch** silent-failure patterns before code ships — MERGE overwrite,
  LAG-inside-IF, missing `retain` on accumulators, macro-quoting errors,
  `PROC APPEND` shape mismatches, and more
- **Enforce** the 15 rules from `sasjs/lint` v2.4.3 covering macro
  definition, file headers, line formatting, and source hygiene
- **Apply** `sasjs/core` macro patterns — positional-required +
  keyword-optional signatures, `%local` discipline, `iftrue=` guards,
  `/*/STORE SOURCE*/` registration
- **Route** to topic-specific reference files for deep dives

## Installation

### Option 1: Personal scope — all projects (recommended)

Install once into `~/.claude/skills/` and the skill loads for every
Claude Code session on this machine. Pull periodically to pick up new
rules and idioms.

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/xiaosongz/sas94-skill.git ~/.claude/skills/sas94
# later:
git -C ~/.claude/skills/sas94 pull
```

### Option 2: Per-project scope — pin a version

Use this when you want a SAS project to ride on a specific skill version,
independent of your personal skills directory.

```bash
mkdir -p .claude/skills
git clone https://github.com/xiaosongz/sas94-skill.git .claude/skills/sas94
rm -rf .claude/skills/sas94/.git
```

### Option 3: Plugin marketplace — `/plugin install sas94`

Planned for `v0.0.2+`. Once published to the Claude Code plugin
marketplace, install will collapse to `/plugin install sas94`. Not yet
available.

### Ad-hoc: `claude --add-dir <path>`

Power-user invocation for one-off skill loading from a non-standard
directory — pass `--add-dir /path/to/sas94-skill` at CLI launch and
Claude Code will treat that path as an additional skill root for the
session.

The skill activates on `.sas` files (via the `paths: "**/*.sas"`
frontmatter entry) and on SAS-flavored prompt keywords (see `SKILL.md`
for the full trigger list).

## Usage

### Example prompts

```text
Write a SAS macro that returns an unused libref name, following sasjs/core
conventions.
```

```text
Merge two claims datasets by member_id; both carry a `paid_amt` column —
make sure the left-side value is preserved.
```

```text
Review my macro for %local discipline and quote-function usage.
```

```text
Help me debug a PROC APPEND that errors with "Variable X in DATA set not in
BASE set."
```

```text
Write a DATA step that computes a lagged diagnosis-date difference, only
for index events.
```

## Contents

```text
sas94-skill/
├── SKILL.md                               # Thin router — trigger, routing table, workflow
├── .skillignore                           # Excludes pipeline/ and docs/design.md from install
├── assets/
│   ├── data-step-template.sas             # DATA step skeleton with Doxygen header
│   ├── proc-sql-template.sas              # PROC SQL skeleton
│   ├── macro-template.sas                 # %macro / %mend skeleton with parenthesized sig
│   └── analysis-template.sas              # End-to-end study-program scaffold
├── references/                            # Loaded on-demand per routing table
│   ├── sas-master-reference.md            # Top-20 rules; load for new .sas files
│   ├── data-step.md                       # MERGE/BY, first./last., retain, arrays, PDV
│   ├── macros.md                          # %let, %macro scope, quoting, &&var
│   ├── proc-sql.md                        # Joins, dedup, INTO :macvar, RESET
│   ├── base-procs.md                      # FREQ, MEANS, UNIVARIATE, SORT, TRANSPOSE
│   ├── stat-procs.md                      # LOGISTIC, GLM, MIXED, GENMOD, SURVEY*
│   ├── hash-tables.md                     # declare hash, definekey, hashiter
│   ├── ods-and-output.md                  # ODS RTF/EXCEL/PDF, ODS OUTPUT, GTL
│   ├── formats-informats.md               # PROC FORMAT, date/time, input()/put()
│   ├── functions-dates.md                 # Date/time/datetime functions (INTNX, INTCK, MDY, DATEPART)
│   ├── functions-strings.md               # String functions (SCAN, SUBSTR, CATX, COMPRESS, TRANWRD)
│   ├── functions-numeric.md               # Numeric and array functions (SUM, ROUND, MOD, DIM)
│   └── idioms-from-lexjansen.md           # SUGI / SAS Global Forum idioms
└── docs/
    ├── design.md                          # Architecture and sourcing strategy
    ├── CONTRIBUTING.md                    # Reviewer workflow, PR + issue templates
    ├── rule-provenance.md                 # Auto-generated audit trail (rule → source URL)
    └── coverage-matrix.md                 # Auto-generated reference-file coverage report
```

## Critical Rules (Summary)

The top-5 rules below are enforced across every SAS file the skill
writes. See
[`references/macros.md`](references/macros.md) and
[`references/data-step.md`](references/data-step.md) for the full set
(6 + 6 rules plus 20 aggregated top-level rules in
[`references/sas-master-reference.md`](references/sas-master-reference.md)).

| # | Rule | Reference |
|---|------|-----------|
| 1 | `LOGISTIC` models `P(Y = lowest ordinal value)` by default — pin the event with `descending` or `event='value'` | [stat-procs.md §Rule 2](references/stat-procs.md) |
| 2 | `GENMOD` defaults to `DIST=NORMAL LINK=IDENTITY` — specify both for logistic, Poisson, or gamma | [stat-procs.md §Rule 3](references/stat-procs.md) |
| 3 | MERGE silently overwrites same-named columns — rename on input, then coalesce | [data-step.md §MERGE overwrite](references/data-step.md) |
| 4 | `LAG` is queue-based — call unconditionally, gate usage afterwards | [data-step.md §LAG trap](references/data-step.md) |
| 5 | Every `%macro` must carry parentheses `()`; declare `%local` for every non-parameter symbol | [macros.md §Rule 1](references/macros.md) |

Full rule list with `CORRECT` / `WRONG` code examples and source URLs:
[`docs/rule-provenance.md`](docs/rule-provenance.md).

## Evaluation

A small regression-baseline eval lives in `evals/`. Three prompts, one per
claimed differentiator of the skill vs. a generic LLM writing SAS
(`sasjs/core` macro conventions, PROC APPEND silent-failure patterns,
PROC LOGISTIC event pinning + ODS OUTPUT). The harness is **manual** —
the maintainer runs each prompt inside a fresh Claude Code session with
the skill installed, saves Claude's reply to `evals/transcripts/<id>.txt`,
then a stdlib-only Python runner pattern-checks the transcripts. No API
key, no SDK dependency, no per-run cost.

Run before tagging a new version:

```bash
uv --directory pipeline run python ../evals/run_evals.py
```

See [`docs/EVALS.md`](docs/EVALS.md) for why it's a manual harness and
[`evals/README.md`](evals/README.md) for the full how-to.

## Contributing

See [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) for the reviewer
workflow, PR template, and issue template for rule disputes. Content
contributions to `references/*.md` are the primary contribution path —
every new Rule or Idiom must carry a `Source:` URL on the line
immediately following the heading.

For pipeline internals — how rules and idioms are sourced, how to refresh
SAS-doc scrapes at a new Mx release, how to add a new lexjansen paper, and
how to reuse the pattern for other under-represented-language skills —
see [`docs/BUILDING.md`](docs/BUILDING.md).

## License

[MIT](LICENSE)
