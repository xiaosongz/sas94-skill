---
title: PROC SQL reference index
loaded_when: '"PROC SQL", "SELECT", "LEFT JOIN" / "INNER JOIN" / "FULL JOIN", "INTO :", "dictionary.", "join claims", "dedup", or any PROC SQL authoring or debugging task.'
---

PROC SQL is Base SAS's implementation of ANSI SQL with SAS-specific extensions
for dataset options, formats, functions, and macro-variable plumbing. Unlike
DATA-step MERGE, a PROC SQL join does not require pre-sorting, does not
overwrite same-named columns silently (they become ambiguous references
instead), and can combine up to 256 tables in a single query.

Most "PROC SQL is slow / wrong" reports resolve to one of three classes:
(1) row explosion from a many-to-many join mistaken for one-to-many,
(2) ambiguous columns in the SELECT list because `a.*, b.*` pulled the
same column from both sides, or (3) a `GROUP BY` / `HAVING` combination
that silently re-merges grouped statistics back onto detail rows.

## Routing table

| Atom | Load when you see / need |
|------|-------------------------|
| `joins.md` | INNER / LEFT / RIGHT / FULL / cross joins; qualifying same-named columns; unqualified-comma-join silent Cartesian; COALESCE for shared payloads and FULL-JOIN keys |
| `dedup.md` | SELECT DISTINCT, GROUP BY + HAVING for dedup, earliest-row-per-key idioms, DISTINCT vs PROC SORT NODUPKEY tradeoffs |
| `into-macvar.md` | `INTO :mv`, `INTO :list1-:listN`, `SEPARATED BY`, NOTRIM/TRIM, dynamic-SQL patterns, dictionary-table list builders |
| `case-expressions.md` | Simple CASE vs searched CASE (simple = equality only); ELSE catch-all; derived column classification |
| `reset-and-options.md` | `RESET`, `NOEXEC`, `FEEDBACK`, `NUMBER`; WHERE vs HAVING; CREATE TABLE AS vs INSERT; remerge warning |

## Cross-topic pointers (prose only)

- DATA-step MERGE vs SQL join semantics — `../data-step/sql-vs-merge.md`.
- `PROC SORT NODUPKEY` vs `SELECT DISTINCT` dedup comparison — `../base-procs/proc-sort.md`.
- Macro-variable consumers of `INTO :mv` (`%let`, `call symputx`, `symget`) —
  `../macros/scope-and-quoting.md` and `../macros/sysfunc-and-eval.md`.
- Schema introspection via `dictionary.columns` or `sashelp.vcolumn` —
  `../base-procs/schema-utils.md`.
