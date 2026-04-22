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
  version: "0.0.1"
---

## When to Use

Activate this skill when the user asks to:

- Write, review, or modify any `.sas` file
- Translate a study description into a SAS 9.4 program (DATA step, PROC SQL, macros)
- Debug a SAS program producing unexpected results, log errors, warnings, or NOTE-level diagnostics
- Build or repair a macro: `%macro` scope, `%let`, `%sysfunc`, quoting (`%str`, `%nrstr`, `%bquote`, `%superq`), `&&var`, `call symput`, `symget()`
- Author DATA step logic with MERGE/BY, `first.`/`last.`, `retain`, arrays, hash objects, PDV reasoning
- Write or audit PROC SQL (joins, dedup, `INTO :macvar`, `RESET`)
- Run base procs (FREQ, MEANS, UNIVARIATE, SORT, TRANSPOSE, REPORT) or statistical procs (LOGISTIC, GLM, MIXED, GENMOD, SURVEY\*, LIFETEST)
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

## Critical Rules (Summary)

Top-20 aggregated rules (macros + DATA step + GWU items) live in `references/sas-master-reference.md`; per-topic rules live in the matching topic file. Consult the routing table below and load the relevant reference file before writing or reviewing SAS code. **Do not attempt to answer SAS questions from SKILL.md alone.**

## STOP and Re-check — Known Silent-Failure Patterns

Stop and load the indicated reference file before writing or reviewing code when you see any of these patterns. Each pattern is a documented SAS footgun that compiles or runs cleanly but produces wrong results or bypasses a guardrail.

- **`data a; set b; a = b + c; run;` without `retain`** — STOP. First row writes an uninitialized accumulator. Load `references/data-step.md` for retain-behavior and PDV-initialization rules.
- **`%macro foo; ... %mend;` missing `()` in the macro signature** — STOP. `sasjs/lint hasMacroParentheses` forbids this; silent-parameter bugs follow. Load `references/macros.md`.
- **`proc sql; create table t as select * from a, b;` (unqualified comma join)** — STOP. This is a cartesian product, not a join. Load `references/proc-sql.md`.
- **`merge a b; by id; run;` without handling `first.`/`last.`** — STOP. Right-table values silently overwrite left-table values on duplicate keys. Load `references/data-step.md` MERGE/BY rules.
- **`declare hash h(); h.definekey(); h.definedata(); h.definedone();` without `length` declared for key/data vars upstream** — STOP. Hash vars inherit PDV length; undeclared → truncation. Load `references/hash-tables.md`.
- **`%let x = &y;` inside `%macro` without scope audit** — STOP. Implicit global-scope write when `y` resolves at outer scope. Load `references/macros.md` scope-and-quoting rules.

## Reference Routing

Load the appropriate reference file based on the task or trigger phrase. This is the authoritative routing table for the skill.

| Task / Trigger Phrase | Load Reference | Also Load If |
|-----------------------|---------------|--------------|
| New `.sas` file, study program skeleton | `sas-master-reference.md` | + domain file per section |
| "MERGE", "BY processing", "first.", "last.", "retain", "array", "PDV" | `data-step.md` | `functions-dates.md` / `functions-strings.md` / `functions-numeric.md` if fns involved |
| "PROC SQL", "join claims", "dedup", "INTO :macvar" | `proc-sql.md` | `macros.md` if INTO drives macro |
| "%macro", "%let", "%sysfunc", quoting error, `&&var`, symget/symput | `macros.md` | `sas-master-reference.md` for scope rules |
| PROC FREQ / MEANS / UNIVARIATE / SORT / TRANSPOSE / REPORT | `base-procs.md` | `ods-and-output.md` if capturing output |
| PROC LOGISTIC / GLM / MIXED / GENMOD / SURVEY* / LIFETEST | `stat-procs.md` | `ods-and-output.md` for ODS OUTPUT |
| "hash join", "hash lookup", `declare hash`, `definekey`, `hashiter` | `hash-tables.md` | `data-step.md` for DATA-step context |
| ODS RTF/EXCEL/PDF, ODS OUTPUT, ODS GRAPHICS, GTL | `ods-and-output.md` | `stat-procs.md` if capturing proc output |
| PROC FORMAT, date/time fns, picture formats, `input()`/`put()` | `formats-informats.md` | `functions-dates.md` |
| "INTNX", "INTCK", "date arithmetic", "TODAY", "MDY", "DATEPART", "YEAR"/"MONTH"/"DAY" | `functions-dates.md` | `formats-informats.md` for PUT / INPUT around dates |
| "SCAN", "SUBSTR", "CATX", "CATS", "COMPRESS", "TRANWRD", "INDEX", "FIND", string parsing | `functions-strings.md` | `macros.md` for `%SCAN` / `%SUBSTR` / quoting |
| "ROUND", "MOD", "SUM function", "MEAN" (row-wise), "DIM", "HBOUND", "LBOUND", array inspection | `functions-numeric.md` | `base-procs.md` for PROC MEANS column aggregates |
| Unknown/novel, "how do SAS programmers do X" | `idioms-from-lexjansen.md` | + best-match topic file |

## Assets

Use these templates as starting points — they supply header comment blocks, not logic. Fill in body idioms by loading the relevant reference file per the routing table above.

- `assets/data-step-template.sas` — generic DATA step skeleton
- `assets/proc-sql-template.sas` — PROC SQL skeleton
- `assets/macro-template.sas` — `%macro` / `%mend` skeleton with parenthesized signature
- `assets/analysis-template.sas` — end-to-end study-program scaffold

## Workflow

1. Identify the trigger (file type, keyword, or explicit request) and match it to a row in the Reference Routing table.
2. Load the indicated reference file — not SKILL.md — before writing or reviewing any non-trivial code.
3. Apply the STOP-and-Re-check patterns above as a pre-flight check for the most common silent-failure classes.
4. For new files, start from the matching `assets/*.sas` template.
5. When a pattern does not clearly match one reference, start with `references/idioms-from-lexjansen.md` for real-world idioms, then branch to the topic file.

**Shell commands.** Skill does not execute SAS. Reference files suggest diagnostic shell commands (`hexdump`, `file`) for inspecting `.sas` bytes — Bash not pre-approved, prompts at project scope.
