---
name: sas94
description: >
  Use when user references a .sas file, SAS 9.4 code, DATA step constructs
  (MERGE/BY, first./last., retain, arrays, hash objects), PROC SQL, SAS macros
  (%macro, %sysfunc, quoting, symput/symget), base or stat procs
  (FREQ/MEANS/LOGISTIC/GLM/MIXED/GENMOD/SURVEY*/LIFETEST), ODS RTF/EXCEL/PDF,
  or PROC FORMAT. Not for R, Python, Stata, SPSS, generic SQL, Procfile, or
  git merges.
license: MIT
compatibility: Designed for Claude Code; does not execute SAS
allowed-tools: Read Grep Glob Write Edit
metadata:
  author: Xiaosong Zhang
  repository: https://github.com/xiaosongz/sas94-skill
  version: "0.1.0-beta.1"
---

## When to Use

Activate this skill when the user asks to:

- Write, review, or modify any `.sas` file
- Translate a study description into a SAS 9.4 program (DATA step, PROC SQL, macros)
- Debug a SAS program producing unexpected results, log errors, warnings, or NOTE-level diagnostics
- Build or repair a macro: `%macro` scope, `%let`, `%sysfunc`, quoting (`%str`, `%nrstr`, `%bquote`, `%superq`), `&&var`, `call symput`, `symget()`
- Author DATA step logic with MERGE/BY, `first.`/`last.`, `retain`, arrays, hash objects, PDV reasoning
- Write or audit PROC SQL (joins, dedup, `INTO :macvar`, `RESET`)
- Run base procs (FREQ, MEANS, UNIVARIATE, SORT, TRANSPOSE, REPORT, CONTENTS, DATASETS, IMPORT, EXPORT, COMPARE) or statistical procs (LOGISTIC, GLM, MIXED, GENMOD, SURVEY\*, LIFETEST, PHREG)
- Capture proc output via ODS (RTF, EXCEL, PDF, ODS OUTPUT, ODS GRAPHICS, GTL)
- Build PROC FORMAT value/picture formats, or use date/time functions and `input()`/`put()` conversions
- Look up SAS function signatures (date arithmetic, string manipulation, numeric)

Prefer this skill whenever the current file or referenced path is a `.sas` file, or when the user references SAS 9.4 code (DATA step, PROC SQL, %macro, ODS, hash tables, etc.).

## When NOT to Use

Skip even if keywords overlap — another skill or a generic response fits:

- R (dplyr, tidyverse, data.frame)
- Python (pandas, dataframe)
- Stata, SPSS
- Generic SQL (T-SQL, PostgreSQL, BigQuery)
- Procfile or shell "proc" commands
- Git merges — even when the user says "merge", "array", "dataframe", or "proc"

## How to Use This Skill

References are organized as per-concept **atoms** under `references/<topic>/<atom>.md`, each ~100-200 lines, each carrying one to three Critical Rules plus CORRECT / WRONG code pairs. **Load only the atom(s) your task actually needs.** The Reference Routing table below is the authoritative map. Do not answer SAS questions from SKILL.md alone.

When the routing table is ambiguous, load the topic's `_index.md` first (cheap — 30-50 lines) and branch from there.

**Base documentation URL** (use when a reference atom is insufficient): [documentation.sas.com/doc/en/pgmsascdc/9.4_3.5/](https://documentation.sas.com/doc/en/pgmsascdc/9.4_3.5/) — browse or general web search.

## STOP and Re-check — Known Silent-Failure Patterns

Stop and load the indicated atom before writing or reviewing code when you see any of these patterns. Each pattern is a documented SAS footgun that compiles or runs cleanly but produces wrong results or bypasses a guardrail.

- **`data a; set b; a = b + c; run;` without `retain`** — STOP. First row writes an uninitialized accumulator. Load `references/data-step/retain-pdv.md`.
- **`%macro foo; ... %mend;` missing `()` in the macro signature** — STOP. `sasjs/lint hasMacroParentheses` forbids this; silent-parameter bugs follow. Load `references/macros/definition-syntax.md`.
- **`proc sql; create table t as select * from a, b;` (unqualified comma join)** — STOP. This is a Cartesian product, not a join. Load `references/proc-sql/joins.md`.
- **`merge a b; by id; run;` with shared payload column names** — STOP. Right-table values silently overwrite left-table values on duplicate keys. Load `references/data-step/merge.md`.
- **`declare hash h(); h.definekey(...); h.definedata(...); h.definedone();` without `length` declared for key/data vars upstream** — STOP. Hash vars inherit PDV length; undeclared → truncation. Load `references/hash-tables/declare-and-length.md`.
- **`%let x = &y;` inside `%macro` without `%local x;`** — STOP. Implicit outer-scope write when `x` exists at the caller's level. Load `references/macros/scope-and-quoting.md`.
- **`where derived_var = ...;` after computing `derived_var` in the DATA step** — STOP. WHERE is pre-PDV and cannot see derived columns. Load `references/data-step/where-vs-if.md`.
- **`proc datasets lib=<lib> kill;`** — STOP. Empties the library with no confirmation, no prompt. Load `references/base-procs/schema-utils.md`.
- **`proc import datafile='f.csv' out=ds;` with no `DBMS=` / `GUESSINGROWS=MAX`** — STOP. Default `GUESSINGROWS=1` for CSV truncates row-1-short strings. Load `references/base-procs/file-io.md`.
- **`%put '&var';` expecting single quotes to suppress resolution** — STOP. Macro processor tokenizes before the statement receives its argument. Load `references/data-step/macro-quoting.md`.

## Reference Routing

Load the specific atom matching the trigger. Only load a topic's `_index.md` when the trigger is ambiguous across atoms within that topic.

### Base SAS procedures

| Trigger | Load |
|---|---|
| `PROC FREQ`, cross-tab, missing handling | `references/base-procs/proc-freq.md` |
| `PROC MEANS`, class-level summary, `OUTPUT OUT=` | `references/base-procs/proc-means.md` |
| `PROC UNIVARIATE`, quantiles | `references/base-procs/proc-univariate.md` |
| `PROC SORT`, `NODUPKEY`, `NODUPRECS`, `OUT=` overwrite | `references/base-procs/proc-sort.md` |
| `PROC TRANSPOSE`, long↔wide reshape | `references/base-procs/proc-transpose.md` |
| `PROC REPORT`, `DEFINE`, grouping | `references/base-procs/proc-report.md` |
| `PROC PRINT`, `NOOBS`, listing | `references/base-procs/proc-print.md` |
| `PROC CONTENTS`, `PROC DATASETS`, `KILL`, schema inspection | `references/base-procs/schema-utils.md` |
| `PROC IMPORT`, `PROC EXPORT`, `DBMS=`, `GUESSINGROWS=`, CSV / Excel IO | `references/base-procs/file-io.md` |
| `PROC COMPARE`, dataset equality, `CRITERION=`, `METHOD=` | `references/base-procs/proc-compare.md` |

### DATA step

| Trigger | Load |
|---|---|
| `MERGE`, BY processing, same-name overwrite, `coalesce` | `references/data-step/merge.md` |
| `LAG`, queue semantics, conditional LAG | `references/data-step/lag.md` |
| `PROC APPEND`, BASE / DATA shape, `FORCE` | `references/data-step/append.md` |
| PROC SQL join vs DATA-step MERGE tradeoff | `references/data-step/sql-vs-merge.md` |
| `retain`, accumulator, PDV initialization | `references/data-step/retain-pdv.md` |
| `WHERE` vs subsetting `IF`, compile-time vs execute-time filter | `references/data-step/where-vs-if.md` |
| DATA-step single-quote vs double-quote string, `%nrstr` masking | `references/data-step/macro-quoting.md` |
| `sasjs/lint` file hygiene: indent, tabs, trailing space, gremlins, encoded passwords | `references/data-step/file-hygiene.md` |

### Macros

| Trigger | Load |
|---|---|
| `%macro` / `%mend` signature, parens, nesting, Doxygen, required options | `references/macros/definition-syntax.md` |
| `%local`, `%global`, quoting (`%str`, `%nrstr`, `%bquote`, `%superq`), `&&var`, `call symputx`, `symget` | `references/macros/scope-and-quoting.md` |
| `OPTIONS MPRINT / MLOGIC / SYMBOLGEN`, `OBS=0`, `%PUT _USER_` / `_ALL_`, macro debugging | `references/macros/debugging.md` |
| `%INCLUDE` vs `%MACRO` vs `SET` — file inclusion vs parameterized reuse | `references/macros/include-vs-macro.md` |
| `%sysfunc`, `%eval`, `%sysevalf`, macro arithmetic | `references/macros/sysfunc-and-eval.md` |

### Statistical procedures

| Trigger | Load |
|---|---|
| `PROC LOGISTIC`, `event='1'`, `descending`, CLASS reference coding | `references/stat-procs/proc-logistic.md` |
| `PROC GLM`, ANCOVA, `LSMEANS`, Type III SS | `references/stat-procs/proc-glm.md` |
| `PROC MIXED`, `RANDOM` vs `REPEATED`, `SUBJECT=` | `references/stat-procs/proc-mixed.md` |
| `PROC GENMOD`, `DIST=` / `LINK=`, GEE, offset | `references/stat-procs/proc-genmod.md` |
| `PROC LIFETEST`, Kaplan-Meier, TIME censor code | `references/stat-procs/proc-lifetest.md` |
| `PROC PHREG`, Cox PH, `HAZARDRATIO` | `references/stat-procs/proc-phreg.md` |
| `PROC SURVEYMEANS` / `SURVEYFREQ` / `SURVEYLOGISTIC` / `SURVEYREG`, design vars | `references/stat-procs/proc-surveymeans.md` |

### Hash tables

| Trigger | Load |
|---|---|
| `declare hash`, `definekey`, `definedata`, `definedone`, PDV length match | `references/hash-tables/declare-and-length.md` |
| `find()`, `check()`, return-code guard, `call missing()` reset | `references/hash-tables/find-check-rc.md` |
| `hiter`, `first()`, `next()`, hash iteration, `output()` | `references/hash-tables/iteration.md` |
| `multidata: 'Y'`, duplicate-key handling, default first-row-only trap | `references/hash-tables/multidata.md` |
| Dorfman streaming lookup, hash dedup, in-memory aggregator/counter | `references/hash-tables/idioms.md` |

### PROC SQL

| Trigger | Load |
|---|---|
| Joins, `COALESCE`, qualified columns, Cartesian trap | `references/proc-sql/joins.md` |
| `DISTINCT`, `GROUP BY`, `HAVING`, dedup | `references/proc-sql/dedup.md` |
| `INTO :mv`, `INTO :list`, `SEPARATED BY`, dictionary tables | `references/proc-sql/into-macvar.md` |
| `CASE WHEN` (searched vs simple), `ELSE` | `references/proc-sql/case-expressions.md` |
| `RESET`, `FEEDBACK`, `NOEXEC`, `CREATE TABLE AS` | `references/proc-sql/reset-and-options.md` |

### ODS and output

| Trigger | Load |
|---|---|
| `ODS OUTPUT Table=ds;`, `ODS TRACE`, capture proc output to dataset | `references/ods-and-output/ods-output-capture.md` |
| `ODS RTF` / `ODS PDF` / `ODS EXCEL` / `ODS CSVALL`, destinations, `style=` | `references/ods-and-output/ods-destinations.md` |
| `ODS GRAPHICS`, `imagename=`, GTL / `proc template` | `references/ods-and-output/ods-graphics.md` |
| `ODS SELECT` / `ODS EXCLUDE`, filter proc tables | `references/ods-and-output/ods-select-exclude.md` |
| `ODS LISTING`, text output, linesize / pagesize | `references/ods-and-output/ods-listing.md` |

### Formats and informats

| Trigger | Load |
|---|---|
| `put()` vs `input()`, `putn/inputn`, trailing dot on reference | `references/formats-informats/put-vs-input.md` |
| `PROC FORMAT`, `VALUE`, `INVALUE`, `PICTURE`, `CNTLIN=` | `references/formats-informats/proc-format.md` |
| `mmddyy10.`, `yymmdd10.`, `date9.`, `datetime20.`, `anydtdte.`, `DATESTYLE=` | `references/formats-informats/date-formats.md` |
| `best.`, `dollar.`, `comma.`, `w.d` precision, truncation | `references/formats-informats/numeric-formats.md` |

### Functions

| Trigger | Load |
|---|---|
| `INTNX`, `INTCK`, interval alignment, count-vs-duration trap | `references/functions-dates/intnx-intck.md` |
| `MDY`, `YEAR`, `MONTH`, `DAY`, `WEEKDAY`, `TODAY` | `references/functions-dates/construction.md` |
| `DATEPART`, `TIMEPART`, date vs datetime scale | `references/functions-dates/datetime-parts.md` |
| Date arithmetic, "add one month" via INTNX vs +30 | `references/functions-dates/date-arithmetic.md` |
| `CATS`, `CATX`, `CATT`, `CAT`, `\|\|` concatenation | `references/functions-strings/concat.md` |
| `SCAN`, `SUBSTR`, `SUBSTRN`, `FIND`, `INDEX`, `COUNTW` | `references/functions-strings/parse.md` |
| `COMPRESS`, `TRANWRD`, `STRIP`, `TRIM`, `LEFT`, `COMPBL` | `references/functions-strings/clean.md` |
| `UPCASE`, `LOWCASE`, `PROPCASE`, string comparison with blanks | `references/functions-strings/case-and-compare.md` |
| `SUM(of ...)`, `MEAN(of ...)`, row-wise aggregates, missing handling | `references/functions-numeric/row-aggregates.md` |
| `ROUND`, `CEIL`, `FLOOR`, `MOD`, `ABS`, precision | `references/functions-numeric/arithmetic.md` |
| `DIM`, `HBOUND`, `LBOUND`, array bounds | `references/functions-numeric/arrays.md` |

### Real-world idioms (fallback)

| Trigger | Load |
|---|---|
| "how do SAS programmers do X", novel / unknown pattern | `references/idioms-from-lexjansen/_index.md` then branch |
| Dorfman hash techniques (streaming lookup, dedup, aggregator) | `references/idioms-from-lexjansen/hash-idioms.md` |
| Lafler CASE expressions, PROC SQL idioms | `references/idioms-from-lexjansen/sql-idioms.md` |
| Whitlock / Lepp macro quoting + dynamic code idioms | `references/idioms-from-lexjansen/macro-idioms.md` |

## Assets

Use these templates as starting points — they supply header comment blocks, not logic. Fill in body idioms by loading the relevant atom per the routing table above.

- `assets/data-step-template.sas` — generic DATA step skeleton
- `assets/proc-sql-template.sas` — PROC SQL skeleton
- `assets/macro-template.sas` — `%macro` / `%mend` skeleton with parenthesized signature
- `assets/analysis-template.sas` — end-to-end study-program scaffold

## Workflow

1. Identify the trigger (file type, keyword, or explicit request) and match it to a row in the Reference Routing table.
2. Load the indicated atom — not SKILL.md — before writing or reviewing any non-trivial code.
3. Apply the STOP-and-Re-check patterns above as a pre-flight check for the most common silent-failure classes.
4. For new files, start from the matching `assets/*.sas` template.
5. When a pattern does not clearly match a single atom, load the topic's `_index.md` first (30-50 lines) then branch to the specific atom. For novel patterns, start with `references/idioms-from-lexjansen/_index.md`.
6. If an atom is insufficient, fall back to the SAS documentation base URL above.

**Shell commands.** Skill does not execute SAS. Atoms suggest diagnostic shell commands (`hexdump`, `file`) for inspecting `.sas` bytes — Bash not pre-approved, prompts at project scope.
