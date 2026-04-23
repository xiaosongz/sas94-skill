---
title: DATA step reference - index
loaded_when: '"DATA step", "MERGE", "BY processing", "first.", "last.", "retain", "array", "PDV", "LAG", "PROC APPEND", "subsetting IF", or any DATA-step authoring or debugging task.'
---

## Routing table

The DATA step is a row-at-a-time iteration over input data with an implicit `OUTPUT` and a Program Data Vector (PDV) that carries state across rows only for `RETAIN`ed variables. Most silent-bug DATA steps are scope errors: a variable that should be retained is not, a MERGE silently overwrites one side, a `LAG` is positioned inside a conditional, or a quoted macro trigger resolves at an unexpected phase. Load the atom matching your task.

| Atom | One-line summary | Load when |
|------|------------------|-----------|
| `merge.md` | Rule 1: MERGE silently right-overwrites same-named columns; rename-on-input + `coalesce` | `MERGE`, BY-group join, same-name payload columns |
| `lag.md` | Rule 2: `LAG` is queue-based — call unconditionally, gate usage after | `LAG`, previous-row value, row-to-row diff |
| `append.md` | Rule 3: PROC APPEND shape rules — missing-from-BASE ERRORs, missing-from-DATA silently nulls | `PROC APPEND`, stacking, `FORCE`, column-mismatch |
| `sql-vs-merge.md` | Rule 4: SQL-join vs MERGE semantics; qualify columns, `coalesce` explicitly | choosing between PROC SQL join and DATA-step MERGE |
| `macro-quoting.md` | Rule 5: DATA-step quotes resolve `&var` in double / literal in single; macro-context needs `%nrstr` | `%put`, `%let`, `&var` in strings, quote masking |
| `retain-pdv.md` | Rule 6: retain accumulators + PDV initialization; plus canonical assertion and `mf_nobs` idioms | accumulator, carry-forward, `retain`, PDV state |
| `where-vs-if.md` | Rule 7: `WHERE` compile-time pre-PDV vs subsetting `IF` execute-time post-PDV | `WHERE`, `IF`, filter on derived column |
| `file-hygiene.md` | Hygiene 1-6: `sasjs/lint` indentation, line length, tabs, trailing whitespace, gremlins, encoded passwords | lint, style, whitespace, invisible-char bugs, secret scanning |

## Cross-topic references

- Macro side of `call symputx` / `symget` / macro-generated DATA-step code: `../macros/scope-and-quoting.md`.
- SQL-join mechanics (GROUP BY, remerging, subqueries): see prose references to PROC SQL.
- Hash-lookup alternative to MERGE for reference-table joins: see prose references to hash tables.
- Upstream GWU transcription feeding Rules 1-5: `pipeline/manual/gwu-data-mining-5-items.md`.
