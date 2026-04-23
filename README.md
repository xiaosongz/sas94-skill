# sas94-skill

A [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skill for
writing, reviewing, and debugging SAS 9.4 code with AI assistance.

SAS 9.4 is the daily driver for biostatisticians, health-services
researchers, and pharma/claims analysts, yet SAS is underrepresented in LLM
training corpora. This skill distills rules and idioms from MIT-licensed
sources (`sasjs/lint`, `sasjs/core`) plus hand-transcribed SAS-programmer
pitfalls (GWU data-mining curriculum), and routes Claude Code to
topic-specific reference files on demand.

**Status:** `v0.0.1` pre-release. Reference content is organized as
per-topic atom directories under `references/`, with each atom covering
one concept (e.g. `references/data-step/merge.md`,
`references/macros/scope-and-quoting.md`). Atoms are populated across
both REQUIRED sections (Overview, Critical Rules, Canonical Idioms,
Function/Statement Quick Ref, See Also) and OPTIONAL sections (Silent
Pitfalls, Anti-patterns). See
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

### Recommended: Claude Code plugin marketplace

Two slash commands inside any Claude Code session:

```text
/plugin marketplace add xiaosongz/sas94-skill
/plugin install sas94@sas94-skill
```

Claude Code fetches this repo, installs the `sas94` plugin into the
local plugin cache, and activates the skill. Update later with:

```text
/plugin marketplace update sas94-skill
```

Skill activates on `.sas` files and SAS-flavored prompt keywords — see
`plugins/sas94/skills/sas94/SKILL.md` for the full trigger list.

### Alternative: personal-scope git clone

Prefer `git` over slash commands? Clone the skill subtree into your
personal skills directory (one line):

```bash
git clone --depth 1 https://github.com/xiaosongz/sas94-skill.git /tmp/sas94-skill && mkdir -p ~/.claude/skills && mv /tmp/sas94-skill/plugins/sas94/skills/sas94 ~/.claude/skills/sas94 && rm -rf /tmp/sas94-skill
```

Update later by re-running the same command. The plugin marketplace
path is cleaner — use it unless you have a reason not to.

### Ad-hoc: `claude --add-dir <path>`

Power-user invocation for one-off skill loading. Clone the repo
anywhere, then:

```bash
claude --add-dir /path/to/sas94-skill/plugins/sas94/skills/sas94
```

Claude Code treats that path as an additional skill root for the
session only.

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
sas94-skill/                                      # repo = marketplace
├── .claude-plugin/
│   └── marketplace.json                          # marketplace catalog (lists the sas94 plugin)
├── plugins/
│   └── sas94/                                    # plugin root (copied into ~/.claude/plugins/cache on install)
│       ├── .claude-plugin/
│       │   └── plugin.json                       # plugin manifest
│       └── skills/
│           └── sas94/                            # skill root
│               ├── SKILL.md                      # Thin router — trigger, routing table, workflow
│               ├── assets/
│               │   ├── data-step-template.sas    # DATA step skeleton with Doxygen header
│               │   ├── proc-sql-template.sas     # PROC SQL skeleton
│               │   ├── macro-template.sas        # %macro / %mend skeleton with parenthesized sig
│               │   └── analysis-template.sas     # End-to-end study-program scaffold
│               └── references/                   # Per-topic atom directories, loaded on-demand per SKILL.md routing table
│                   ├── data-step/                # MERGE/BY, LAG, retain+PDV, APPEND, SQL-vs-MERGE, quoting, file hygiene
│                   ├── macros/                   # %macro/%let, scope+quoting, debugging, %include, %sysfunc/%eval
│                   ├── proc-sql/                 # Joins, dedup, INTO :macvar, CASE, RESET + options
│                   ├── base-procs/               # FREQ, MEANS, UNIVARIATE, SORT, TRANSPOSE, REPORT, PRINT, COMPARE, file I/O
│                   ├── stat-procs/               # LOGISTIC, GLM, MIXED, GENMOD, LIFETEST, PHREG, SURVEYMEANS
│                   ├── hash-tables/              # declare+length, find/check rc, iteration, multidata, idioms
│                   ├── ods-and-output/           # ODS OUTPUT capture, destinations, GRAPHICS, SELECT/EXCLUDE, LISTING
│                   ├── formats-informats/        # PROC FORMAT, put-vs-input, date + numeric formats
│                   ├── functions-dates/          # INTNX/INTCK, construction, datetime parts, date arithmetic
│                   ├── functions-strings/        # concat, parse, clean, case + compare
│                   ├── functions-numeric/        # row aggregates, arithmetic, arrays
│                   └── idioms-from-lexjansen/    # SUGI / SAS Global Forum idioms (hash, SQL, macro)
├── docs/                                         # repo-level docs, not shipped with plugin
│   ├── design.md                                 # Architecture and sourcing strategy
│   ├── CONTRIBUTING.md                           # Reviewer workflow, PR + issue templates
│   ├── rule-provenance.md                        # Auto-generated audit trail (rule → source URL)
│   └── coverage-matrix.md                        # Auto-generated reference-file coverage report
├── evals/                                        # manual transcript-check eval harness
└── pipeline/                                     # extractors + generators for rules/idioms
```

## Critical Rules (Summary)

The top-5 rules below are enforced across every SAS file the skill
writes. See the per-topic atoms under
[`plugins/sas94/skills/sas94/references/macros/`](plugins/sas94/skills/sas94/references/macros/) and
[`plugins/sas94/skills/sas94/references/data-step/`](plugins/sas94/skills/sas94/references/data-step/)
for the full rule set. SKILL.md's routing table is the authoritative
entry point for mapping a task to the right atoms.

| # | Rule | Reference |
|---|------|-----------|
| 1 | `LOGISTIC` models `P(Y = lowest ordinal value)` by default — pin the event with `descending` or `event='value'` | [stat-procs.md §Rule 2](plugins/sas94/skills/sas94/references/stat-procs.md) |
| 2 | `GENMOD` defaults to `DIST=NORMAL LINK=IDENTITY` — specify both for logistic, Poisson, or gamma | [stat-procs.md §Rule 3](plugins/sas94/skills/sas94/references/stat-procs.md) |
| 3 | MERGE silently overwrites same-named columns — rename on input, then coalesce | [data-step.md §MERGE overwrite](plugins/sas94/skills/sas94/references/data-step.md) |
| 4 | `LAG` is queue-based — call unconditionally, gate usage afterwards | [data-step.md §LAG trap](plugins/sas94/skills/sas94/references/data-step.md) |
| 5 | Every `%macro` must carry parentheses `()`; declare `%local` for every non-parameter symbol | [macros.md §Rule 1](plugins/sas94/skills/sas94/references/macros.md) |

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
contributions to `plugins/sas94/skills/sas94/references/*.md` are the primary contribution path —
every new Rule or Idiom must carry a `Source:` URL on the line
immediately following the heading.

For pipeline internals — how rules and idioms are sourced, how to refresh
SAS-doc scrapes at a new Mx release, how to add a new lexjansen paper, and
how to reuse the pattern for other under-represented-language skills —
see [`docs/BUILDING.md`](docs/BUILDING.md).

## License

[MIT](LICENSE)
