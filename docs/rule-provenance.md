# Rule Provenance

Audit trail for every `### Rule` and `### Idiom` heading in `references/*.md`. Each row records the rule's source URL and the `last_reviewed` date from the reference file's frontmatter. This file is auto-generated — do not edit by hand.

Regenerate after editing any reference file:

```bash
uv --directory pipeline run python make_provenance.py > docs/rule-provenance.md
```

| File | Section | # | Claim | Source | Last verified |
|------|---------|---|-------|--------|---------------|
| base-procs.md | Canonical Idioms | idiom | PROC FREQ minimum-count filter via `OUT=` + `WHERE=` | https://documentation.sas.com/doc/en/proc/9.4/proc.htm | 2026-04-21 |
| base-procs.md | Canonical Idioms | idiom | PROC MEANS CLASS-level summary → flat output dataset | https://documentation.sas.com/doc/en/proc/9.4/proc.htm | 2026-04-21 |
| base-procs.md | Canonical Idioms | idiom | PROC SORT NODUPKEY dedup with audit tail | https://documentation.sas.com/doc/en/proc/9.4/proc.htm | 2026-04-21 |
| base-procs.md | Canonical Idioms | idiom | PROC TRANSPOSE long → wide by `ID` | https://documentation.sas.com/doc/en/proc/9.4/proc.htm | 2026-04-21 |
| base-procs.md | Critical Rules | 1 | `PROC FREQ TABLES a*b;` drops rows with missing in `a` or `b` by default — add… | https://documentation.sas.com/doc/en/proc/9.4/proc.htm | 2026-04-21 |
| base-procs.md | Critical Rules | 2 | `PROC MEANS` prints by default — use `NOPRINT` when you only want `OUTPUT OUT=` | https://documentation.sas.com/doc/en/proc/9.4/proc.htm | 2026-04-21 |
| base-procs.md | Critical Rules | 3 | `PROC SORT NODUPKEY` dedups on BY vars only — `NODUPRECS` dedups on the full row | https://documentation.sas.com/doc/en/proc/9.4/proc.htm | 2026-04-21 |
| base-procs.md | Critical Rules | 4 | `PROC SORT` without `OUT=` **replaces** the input dataset in place | https://documentation.sas.com/doc/en/proc/9.4/proc.htm | 2026-04-21 |
| base-procs.md | Critical Rules | 5 | `PROC TRANSPOSE` with no `VAR` transposes every numeric variable — and silently… | https://documentation.sas.com/doc/en/proc/9.4/proc.htm | 2026-04-21 |
| base-procs.md | Critical Rules | 6 | `PROC REPORT DEFINE` type determines aggregation — `DISPLAY` / `ANALYSIS` / `GR… | https://documentation.sas.com/doc/en/proc/9.4/proc.htm | 2026-04-21 |
| base-procs.md | Critical Rules | 7 | `PROC UNIVARIATE` produces a long default report — use `NOPRINT` + `OUTPUT OUT=… | https://documentation.sas.com/doc/en/proc/9.4/proc.htm | 2026-04-21 |
| base-procs.md | Critical Rules | 8 | `PROC PRINT VAR a b c;` orders columns; `NOOBS` drops the row-number column | https://documentation.sas.com/doc/en/proc/9.4/proc.htm | 2026-04-21 |
| data-step.md | Canonical Idioms | idiom | `mf_nobs` — observation-count one-liner for open code | https://github.com/sasjs/core/blob/3a54b9c796c0bfe477d1aefc1e22b9ff9f2c96c2/base/mf_nobs.sas | 2026-04-21 |
| data-step.md | Canonical Idioms | idiom | Guarded predicate macro for DATA-step assertions | https://github.com/sasjs/core/blob/3a54b9c796c0bfe477d1aefc1e22b9ff9f2c96c2/base/mp_assertdsobs.sas | 2026-04-21 |
| data-step.md | Canonical Idioms | idiom | LAG missing-value trap (GWU §1) | https://github.com/jphall663/GWU_data_mining — hand-transcribed in `pipeline/manual/gwu-data-mining-5-items.md`. | 2026-04-21 |
| data-step.md | Canonical Idioms | idiom | Macro resolution and quote semantics (GWU §5) | https://github.com/jphall663/GWU_data_mining — hand-transcribed in `pipeline/manual/gwu-data-mining-5-items.md`. | 2026-04-21 |
| data-step.md | Canonical Idioms | idiom | MERGE overwrite trap (GWU §2) | https://github.com/jphall663/GWU_data_mining — hand-transcribed in `pipeline/manual/gwu-data-mining-5-items.md`. | 2026-04-21 |
| data-step.md | Canonical Idioms | idiom | PROC APPEND variable-shape rules (GWU §3) | https://github.com/jphall663/GWU_data_mining — hand-transcribed in `pipeline/manual/gwu-data-mining-5-items.md`. | 2026-04-21 |
| data-step.md | Canonical Idioms | idiom | SQL join vs MERGE distinction (GWU §4) | https://github.com/jphall663/GWU_data_mining — hand-transcribed in `pipeline/manual/gwu-data-mining-5-items.md`. | 2026-04-21 |
| data-step.md | Critical Rules | 1 | Indent by a consistent multiple of spaces (default 2) — no ad-hoc indentation | https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/line/indentationMultiple.ts | 2026-04-21 |
| data-step.md | Critical Rules | 2 | Keep lines under the configured maximum length (default 300) | https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/line/maxLineLength.ts | 2026-04-21 |
| data-step.md | Critical Rules | 3 | Indent with spaces, never tab characters | https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/line/noTabs.ts | 2026-04-21 |
| data-step.md | Critical Rules | 4 | Strip trailing whitespace from every line | https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/line/noTrailingSpaces.ts | 2026-04-21 |
| data-step.md | Critical Rules | 5 | No "gremlin" non-printable characters | https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/line/noGremlins.ts | 2026-04-21 |
| data-step.md | Critical Rules | 6 | Never commit encoded-password literals (`{SAS001}`, `{SAS002}`, `{SASENC}`) | https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/line/noEncodedPasswords.ts | 2026-04-21 |
| hash-tables.md | Canonical Idioms | idiom | Deduplication via `check()` + `add()` — keep the first row per composite key | https://www.lexjansen.com/nesug/nesug07/ff/ff03.pdf | 2026-04-21 |
| hash-tables.md | Canonical Idioms | idiom | In-memory counter — tally per-key frequencies with `find()` + `replace()` | https://www.lexjansen.com/sugi30/236-30.pdf | 2026-04-21 |
| hash-tables.md | Canonical Idioms | idiom | One-to-many equi-join via `multidata: 'Y'` + `find_next()` | https://www.lexjansen.com/sesug/2015/94_Final_PDF.pdf | 2026-04-21 |
| hash-tables.md | Canonical Idioms | idiom | Reference-table lookup — attach ICD-10 description to every claim row | https://www.lexjansen.com/sugi30/236-30.pdf | 2026-04-21 |
| hash-tables.md | Critical Rules | 1 | The hash must be declared and loaded inside `if _N_ = 1 then do; ... end;` — or… | https://documentation.sas.com/doc/en/lepg/9.4/lepg.htm | 2026-04-21 |
| hash-tables.md | Critical Rules | 2 | Omitting `definedone()` is a silent error — every subsequent method call fails | https://documentation.sas.com/doc/en/lepg/9.4/lepg.htm | 2026-04-21 |
| hash-tables.md | Critical Rules | 3 | Always check the `find()` return code — ignoring it means silent use of the las… | https://www.lexjansen.com/sugi30/236-30.pdf | 2026-04-21 |
| hash-tables.md | Critical Rules | 4 | Hash objects do NOT persist across DATA steps — their lifetime is exactly one s… | https://documentation.sas.com/doc/en/lepg/9.4/lepg.htm | 2026-04-21 |
| hash-tables.md | Critical Rules | 5 | Without `multidata: 'Y'`, only the first row per key loads — silent dedup on th… | https://www.lexjansen.com/sesug/2015/94_Final_PDF.pdf | 2026-04-21 |
| hash-tables.md | Critical Rules | 6 | `add()` fails on a duplicate key; `replace()` overwrites — pick deliberately | https://www.lexjansen.com/sugi30/236-30.pdf | 2026-04-21 |
| hash-tables.md | Critical Rules | 7 | The hash iterator (`hiter`) traverses in order — but `next()`/`prev()` only upd… | https://www.lexjansen.com/sugi30/236-30.pdf | 2026-04-21 |
| hash-tables.md | Critical Rules | 8 | Hash memory grows with the loaded rowcount — claims-scale lookups can OOM the s… | https://www.lexjansen.com/nesug/nesug07/ff/ff03.pdf | 2026-04-21 |
| macros.md | Canonical Idioms | idiom | `%local` discipline — declare every non-parameter symbol at top | https://github.com/sasjs/core/blob/3a54b9c796c0bfe477d1aefc1e22b9ff9f2c96c2/base/mp_hashdataset.sas | 2026-04-21 |
| macros.md | Canonical Idioms | idiom | `/*/STORE SOURCE*/` inline option — one-line signature close | https://github.com/sasjs/core/blob/3a54b9c796c0bfe477d1aefc1e22b9ff9f2c96c2/base/mf_abort.sas | 2026-04-21 |
| macros.md | Canonical Idioms | idiom | Guarded-execution `iftrue=` parameter | https://github.com/sasjs/core/blob/3a54b9c796c0bfe477d1aefc1e22b9ff9f2c96c2/base/mp_hashdataset.sas | 2026-04-21 |
| macros.md | Canonical Idioms | idiom | Positional-required + keyword-optional parameter pattern | https://github.com/sasjs/core/blob/3a54b9c796c0bfe477d1aefc1e22b9ff9f2c96c2/base/mf_existds.sas | 2026-04-21 |
| macros.md | Critical Rules | 1 | Every `%macro` signature must carry parentheses `()` | https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/file/hasMacroParentheses.ts | 2026-04-21 |
| macros.md | Critical Rules | 2 | Close every `%mend` with its macro name | https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/file/hasMacroNameInMend.ts | 2026-04-21 |
| macros.md | Critical Rules | 3 | No nested `%macro` definitions | https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/file/noNestedMacros.ts | 2026-04-21 |
| macros.md | Critical Rules | 4 | Strict macro-definition syntax — no spaces inside parameter names or invalid op… | https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/file/strictMacroDefinition.ts | 2026-04-21 |
| macros.md | Critical Rules | 5 | Every macro file starts with a Doxygen header (`@file`, `@brief`, `@param`, `@v… | https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/file/hasDoxygenHeader.ts | 2026-04-21 |
| macros.md | Critical Rules | 6 | Macros that are shared, stored, or security-sensitive carry required options (`… | https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/file/hasRequiredMacroOptions.ts | 2026-04-21 |
| proc-sql.md | Canonical Idioms | idiom | `INTO :list SEPARATED BY ' '` — build a macro-variable list of column names for… | https://documentation.sas.com/doc/en/proc/9.4/proc.htm | 2026-04-21 |
| proc-sql.md | Canonical Idioms | idiom | Canonical left join — reference-table lookup with `COALESCE` defaulting | https://www.lexjansen.com/mwsug/2015/RF/MWSUG-2015-RF-02.pdf | 2026-04-21 |
| proc-sql.md | Canonical Idioms | idiom | CASE expression for row-level conditional classification | https://www.lexjansen.com/wuss/2011/coders/Papers_Lafler_K_72492.pdf | 2026-04-21 |
| proc-sql.md | Canonical Idioms | idiom | Claims dedup by earliest-row-per-key via `MIN(date)` + self-join | https://www.lexjansen.com/mwsug/2015/RF/MWSUG-2015-RF-02.pdf | 2026-04-21 |
| proc-sql.md | Canonical Idioms | idiom | Dictionary-table introspection — list every variable in every WORK dataset | https://documentation.sas.com/doc/en/proc/9.4/proc.htm | 2026-04-21 |
| proc-sql.md | Critical Rules | 1 | Always qualify shared columns in multi-table SELECT lists — never `a.*, b.*` wi… | https://www.lexjansen.com/mwsug/2015/RF/MWSUG-2015-RF-02.pdf | 2026-04-21 |
| proc-sql.md | Critical Rules | 2 | `FULL JOIN` requires `COALESCE` on the join key — SAS does not merge it automat… | https://www.lexjansen.com/mwsug/2015/RF/MWSUG-2015-RF-02.pdf | 2026-04-21 |
| proc-sql.md | Critical Rules | 3 | `WHERE` filters rows before grouping; `HAVING` filters groups after | https://documentation.sas.com/doc/en/proc/9.4/proc.htm | 2026-04-21 |
| proc-sql.md | Critical Rules | 4 | `INTO :macvar SEPARATED BY ','` needs `%trim` / `strip()` before going into an… | https://documentation.sas.com/doc/en/proc/9.4/proc.htm | 2026-04-21 |
| proc-sql.md | Critical Rules | 5 | Use `FEEDBACK` to surface the expanded query — catches `*` expansion and outer-… | https://www.lexjansen.com/wuss/2011/coders/Papers_Lafler_K_72492.pdf | 2026-04-21 |
| proc-sql.md | Critical Rules | 6 | `NOEXEC` is a dry-run — parses and plans the query without reading data | https://www.lexjansen.com/wuss/2011/coders/Papers_Lafler_K_72492.pdf | 2026-04-21 |
| proc-sql.md | Critical Rules | 7 | `RESET` changes options mid-query block — scope is the current PROC SQL, not th… | https://documentation.sas.com/doc/en/proc/9.4/proc.htm | 2026-04-21 |
| proc-sql.md | Critical Rules | 8 | Prefer `CREATE TABLE t AS SELECT ...` over `CREATE TABLE t (cols)` + `INSERT IN… | https://www.lexjansen.com/mwsug/2015/RF/MWSUG-2015-RF-02.pdf | 2026-04-21 |
| sas-master-reference.md | Critical Rules | 1 | Every `%macro` signature must carry parentheses `()` | https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/file/hasMacroParentheses.ts | 2026-04-21 |
| sas-master-reference.md | Critical Rules | 2 | Close every `%mend` with its macro name | https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/file/hasMacroNameInMend.ts | 2026-04-21 |
| sas-master-reference.md | Critical Rules | 3 | Never nest `%macro` definitions | https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/file/noNestedMacros.ts | 2026-04-21 |
| sas-master-reference.md | Critical Rules | 4 | Use strict macro-definition syntax — no whitespace in parameter names, no unkno… | https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/file/strictMacroDefinition.ts | 2026-04-21 |
| sas-master-reference.md | Critical Rules | 5 | Every `.sas` file begins with a Doxygen header | https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/file/hasDoxygenHeader.ts | 2026-04-21 |
| sas-master-reference.md | Critical Rules | 6 | Security-sensitive or shared macros carry required options (`SECURE`, `STORE SO… | https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/file/hasRequiredMacroOptions.ts | 2026-04-21 |
| sas-master-reference.md | Critical Rules | 7 | Indent by a consistent multiple of spaces (default 2) | https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/line/indentationMultiple.ts | 2026-04-21 |
| sas-master-reference.md | Critical Rules | 8 | Keep lines under the configured maximum length (default 300) | https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/line/maxLineLength.ts | 2026-04-21 |
| sas-master-reference.md | Critical Rules | 9 | Indent with spaces, never tab characters | https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/line/noTabs.ts | 2026-04-21 |
| sas-master-reference.md | Critical Rules | 10 | Strip trailing whitespace from every line | https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/line/noTrailingSpaces.ts | 2026-04-21 |
| sas-master-reference.md | Critical Rules | 11 | No "gremlin" non-printable characters in source | https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/line/noGremlins.ts | 2026-04-21 |
| sas-master-reference.md | Critical Rules | 12 | Never commit encoded-password literals (`{SAS001}`, `{SAS002}`, `{SASENC}`) | https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/line/noEncodedPasswords.ts | 2026-04-21 |
| sas-master-reference.md | Critical Rules | 13 | Use Unix LF (\n) line endings, never CRLF | https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/file/lineEndings.ts | 2026-04-21 |
| sas-master-reference.md | Critical Rules | 14 | LAG is queue-based — call unconditionally, gate usage afterwards (GWU §1) | https://github.com/jphall663/GWU_data_mining — hand-transcribed in `pipeline/manual/gwu-data-mining-5-items.md`. | 2026-04-21 |
| sas-master-reference.md | Critical Rules | 15 | MERGE silently overwrites same-named variables (GWU §2) | https://github.com/jphall663/GWU_data_mining — hand-transcribed in `pipeline/manual/gwu-data-mining-5-items.md`. | 2026-04-21 |
| sas-master-reference.md | Critical Rules | 16 | PROC APPEND variable-shape rules (GWU §3) | https://github.com/jphall663/GWU_data_mining — hand-transcribed in `pipeline/manual/gwu-data-mining-5-items.md`. | 2026-04-21 |
| sas-master-reference.md | Critical Rules | 17 | SQL join vs MERGE — different semantics, different failure modes (GWU §4) | https://github.com/jphall663/GWU_data_mining — hand-transcribed in `pipeline/manual/gwu-data-mining-5-items.md`. | 2026-04-21 |
| sas-master-reference.md | Critical Rules | 18 | Macro resolution and quote semantics (GWU §5) | https://github.com/jphall663/GWU_data_mining — hand-transcribed in `pipeline/manual/gwu-data-mining-5-items.md`. | 2026-04-21 |
| sas-master-reference.md | Critical Rules | 19 | Declare `%local` for every non-parameter symbol inside a macro | https://github.com/sasjs/core/blob/3a54b9c796c0bfe477d1aefc1e22b9ff9f2c96c2/base/mp_hashdataset.sas | 2026-04-21 |
| sas-master-reference.md | Critical Rules | 20 | Structure every macro signature as positional-required + keyword-optional, and… | https://github.com/sasjs/core/blob/3a54b9c796c0bfe477d1aefc1e22b9ff9f2c96c2/base/mf_existds.sas | 2026-04-21 |
| stat-procs.md | Canonical Idioms | idiom | Complex-survey proportion via SURVEYFREQ with STRATA / CLUSTER / WEIGHT | https://documentation.sas.com/doc/en/statug/9.4/statug.htm | 2026-04-21 |
| stat-procs.md | Canonical Idioms | idiom | Cox proportional hazards via PHREG with hazard ratios | https://documentation.sas.com/doc/en/statug/9.4/statug.htm | 2026-04-21 |
| stat-procs.md | Canonical Idioms | idiom | Kaplan-Meier survival curve by treatment with log-rank test | https://documentation.sas.com/doc/en/statug/9.4/statug.htm | 2026-04-21 |
| stat-procs.md | Canonical Idioms | idiom | Logistic regression for a binary claims outcome with CLASS + ODS OUTPUT capture | https://documentation.sas.com/doc/en/statug/9.4/statug.htm | 2026-04-21 |
| stat-procs.md | Canonical Idioms | idiom | Mixed model for panel claims with random patient intercept | https://documentation.sas.com/doc/en/statug/9.4/statug.htm | 2026-04-21 |
| stat-procs.md | Critical Rules | 1 | `CLASS` is required for every categorical predictor — a numeric categorical in… | https://documentation.sas.com/doc/en/statug/9.4/statug.htm | 2026-04-21 |
| stat-procs.md | Critical Rules | 2 | LOGISTIC defaults to modeling `P(Y = lowest ordinal value)` — use `descending`… | https://documentation.sas.com/doc/en/statug/9.4/statug.htm | 2026-04-21 |
| stat-procs.md | Critical Rules | 3 | GENMOD defaults to `DIST=NORMAL LINK=IDENTITY` — specify both for logistic, Poi… | https://documentation.sas.com/doc/en/statug/9.4/statug.htm | 2026-04-21 |
| stat-procs.md | Critical Rules | 4 | MIXED `REPEATED` models R-side (within-subject residual correlation); `RANDOM`… | https://documentation.sas.com/doc/en/statug/9.4/statug.htm | 2026-04-21 |
| stat-procs.md | Critical Rules | 5 | LIFETEST `TIME t*status(code)` — the value in parentheses is the CENSORED code,… | https://documentation.sas.com/doc/en/statug/9.4/statug.htm | 2026-04-21 |
| stat-procs.md | Critical Rules | 6 | SURVEY* procs require design variables — no `STRATA` / `CLUSTER` / `WEIGHT` ass… | https://documentation.sas.com/doc/en/statug/9.4/statug.htm | 2026-04-21 |
| stat-procs.md | Critical Rules | 7 | None of these procs return data to macros — use `ODS OUTPUT` to capture structu… | https://documentation.sas.com/doc/en/statug/9.4/statug.htm | 2026-04-21 |
| stat-procs.md | Critical Rules | 8 | `LSMEANS` in GLM / MIXED / GENMOD produces covariate-adjusted (marginal) means… | https://documentation.sas.com/doc/en/statug/9.4/statug.htm | 2026-04-21 |

Total rows: 93.
