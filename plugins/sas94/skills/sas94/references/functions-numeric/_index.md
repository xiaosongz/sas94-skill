---
title: Numeric and array function reference index
loaded_when: '"SUM function", "MEAN", "MEDIAN", "ROUND", "MOD", "INT", "CEIL", "FLOOR", "LOG", "EXP", "MAX", "MIN", "DIM", "HBOUND", "LBOUND", or any numeric/array function lookup.'
---

Numeric functions are where missing-value arithmetic diverges most from
R, Python, and SQL. `SUM(of x1-x5)` treats missing as zero; `x1+x2+...+x5`
propagates missing. `ROUND(x, 2)` rounds to the nearest even integer —
the second argument is a rounding **unit**, not a decimal-place count.
`MOD(-7, 3)` returns `-1` (sign-of-dividend, like C's `%`), not the
mathematical modulo.

## Routing table

| If you need... | Load |
|----------------|------|
| `SUM(of x1-xN)`, `MEAN`, `MEDIAN`, row-wise `MAX` / `MIN`, `N`, `NMISS` — missing-handling across columns on a single row | `row-aggregates.md` |
| `ROUND`, `INT`, `CEIL`, `FLOOR`, `MOD`, `ABS`, `SIGN`, `LOG`, `EXP` — scalar arithmetic, rounding-unit, sign-of-dividend modulo, precision | `arithmetic.md` |
| `DIM`, `HBOUND`, `LBOUND`, iterating array indices, array vs numeric-variable scoping | `arrays.md` |

## Parallel references (prose only — do not cross-link)

- Date/time functions (`INTNX`, `INTCK`, `DATDIF`) returning numeric
  day-counts that feed the row-wise arithmetic in this topic — see the
  functions-dates topic.
- String functions (`SCAN`, `SUBSTR`, `COMPRESS`, `CATX`) used alongside
  numeric conversions — see the functions-strings topic.

## Column aggregate vs row aggregate

The DATA-step `MAX(a, b, c)` / `MEAN(of x1-xN)` / `SUM(of x1-xN)`
functions are **row-wise** across arguments on one observation. The
`MAX(col)` / `MEAN(col)` / `SUM(col)` expressions inside PROC SQL or
PROC MEANS are **column-wise** across rows. Same names, different
shapes — see `../base-procs/proc-means.md` and
`../proc-sql/joins.md` when you want the column-wise variant.

## Array declaration vs inspection

`DIM` / `HBOUND` / `LBOUND` inspect an array that was declared with an
`array` statement in the DATA step. The declaration itself lives in
`../data-step/retain-pdv.md` (PDV slots) and general DATA-step syntax;
this topic covers only the inspection functions.
