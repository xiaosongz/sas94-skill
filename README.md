# sas94-skill

A [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skill for
writing, reviewing, and debugging SAS 9.4 code with AI assistance.

SAS 9.4 is the daily driver for biostatisticians, health-services
researchers, and pharma/claims analysts, yet SAS is underrepresented in LLM
training corpora. This skill distills rules and idioms from MIT-licensed
sources (`sasjs/lint`, `sasjs/core`) plus hand-transcribed SAS-programmer
pitfalls (GWU data-mining curriculum), and routes Claude Code to
topic-specific reference files on demand.

**Status:** `v0.0.1` pre-release. Three reference files (`macros.md`,
`data-step.md`, `sas-master-reference.md`) are seeded; the other eight are
stubs that will be populated across `v0.0.2`–`v1.0.0`. See
[`docs/coverage-matrix.md`](docs/coverage-matrix.md) for current status.

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

### Option 1: Clone into your project

```bash
mkdir -p .claude/skills
git clone https://github.com/xiaosongz/sas94-skill.git .claude/skills/sas94
rm -rf .claude/skills/sas94/.git
```

### Option 2: Symlink from a central location

```bash
git clone https://github.com/xiaosongz/sas94-skill.git ~/skills/sas94
mkdir -p .claude/skills
ln -s ~/skills/sas94 .claude/skills/sas94
```

The skill activates on `.sas` files and on SAS-flavored prompt keywords
(see `SKILL.md` for the full trigger list).

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
├── permissions.json                       # File-access scope
├── .skillignore                           # Excludes pipeline/ and docs/design.md from install
├── assets/
│   ├── data-step-template.sas             # DATA step skeleton with Doxygen header
│   ├── proc-sql-template.sas              # PROC SQL skeleton
│   ├── macro-template.sas                 # %macro / %mend skeleton with parenthesized sig
│   └── analysis-template.sas              # End-to-end study-program scaffold
├── references/                            # Loaded on-demand per routing table
│   ├── sas-master-reference.md            # Top-20 rules; load for new .sas files        [seeded]
│   ├── data-step.md                       # MERGE/BY, first./last., retain, arrays, PDV  [seeded]
│   ├── macros.md                          # %let, %macro scope, quoting, &&var           [seeded]
│   ├── proc-sql.md                        # Joins, dedup, INTO :macvar, RESET            [stub]
│   ├── base-procs.md                      # FREQ, MEANS, UNIVARIATE, SORT, TRANSPOSE     [stub]
│   ├── stat-procs.md                      # LOGISTIC, GLM, MIXED, GENMOD, SURVEY*        [stub]
│   ├── hash-tables.md                     # declare hash, definekey, hashiter            [stub]
│   ├── ods-and-output.md                  # ODS RTF/EXCEL/PDF, ODS OUTPUT, GTL           [stub]
│   ├── formats-informats.md               # PROC FORMAT, date/time, input()/put()        [stub]
│   ├── functions-reference.md             # Function cheatsheet by category              [stub]
│   └── idioms-from-lexjansen.md           # SUGI / SAS Global Forum idioms               [stub]
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
| 1 | Every `%macro` signature must carry parentheses `()` | [macros.md §Rule 1](references/macros.md) |
| 2 | Close every `%mend` with its macro name | [macros.md §Rule 2](references/macros.md) |
| 3 | Declare `%local` for every non-parameter macro symbol | [sas-master-reference.md §Rule 19](references/sas-master-reference.md) |
| 4 | MERGE silently overwrites same-named columns — rename on input, then coalesce | [data-step.md §MERGE overwrite](references/data-step.md) |
| 5 | `LAG` is queue-based — call unconditionally, gate usage afterwards | [data-step.md §LAG trap](references/data-step.md) |

Full rule list with `CORRECT` / `WRONG` code examples and source URLs:
[`docs/rule-provenance.md`](docs/rule-provenance.md).

## Contributing

See [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) for the reviewer
workflow, PR template, and issue template for rule disputes. Content
contributions to `references/*.md` are the primary contribution path —
every new Rule or Idiom must carry a `Source:` URL on the line
immediately following the heading.

## License

[MIT](LICENSE)
