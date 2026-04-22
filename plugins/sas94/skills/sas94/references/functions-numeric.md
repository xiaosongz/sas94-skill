---
title: SAS numeric and array function reference
scope: Numeric and array-inspection function cheatsheet — SUM, MEAN, MEDIAN, ROUND, INT/CEIL/FLOOR, MOD, LOG/EXP, MAX/MIN (row-wise), DIM, HBOUND/LBOUND. Focused on missing-aware semantics, rounding-unit confusion, and sign-of-dividend MOD behavior that produce silent bugs in claims-data numeric pipelines.
loaded_when: '"SUM function", "MEAN", "MEDIAN", "ROUND", "MOD", "INT", "CEIL", "FLOOR", "LOG", "EXP", "MAX", "MIN", "DIM", "HBOUND", "LBOUND", or any numeric/array function lookup.'
last_reviewed: 2026-04-22
reviewer: xiaosongz
---

## Overview

Numeric functions are where missing-value arithmetic diverges most
from R, Python, and SQL. `SUM(of x1-x5)` treats missing as zero;
`x1+x2+...+x5` propagates missing. `ROUND(x, 2)` rounds to the
nearest even integer — the second argument is a rounding **unit**,
not a decimal-place count. `MOD(-7, 3)` returns `-1` (sign-of-dividend,
like C's `%`), not the mathematical modulo. This file covers row-wise
aggregation (`SUM`, `MEAN`, `MEDIAN`), rounding (`ROUND`,
`INT`, `CEIL`, `FLOOR`), modulo (`MOD`), transcendentals (`LOG`,
`EXP`), row-wise extremes (`MAX`, `MIN`), and array shape (`DIM`,
`HBOUND`, `LBOUND`). Every rule and idiom cites the `SAS Functions
and CALL Routines: Reference` docset (`lefunctionsref`).

For date and string functions see `functions-dates.md` and
`functions-strings.md`. For PROC-level column aggregates (contrast
with the row-wise `MAX` / `MEAN` / `SUM` here) see `base-procs.md`
(`PROC MEANS` / `PROC UNIVARIATE`) and `proc-sql.md`.

## Contents

- [Critical Rules](#critical-rules)
- [Canonical Idioms](#canonical-idioms)
- [Function / Statement Quick Ref](#function--statement-quick-ref)
- [Silent Pitfalls](#silent-pitfalls)
- [Anti-patterns (STOP signs)](#anti-patterns-stop-signs)
- [See Also](#see-also)

## Critical Rules

### Rule 1: `SUM(of x1-x5)` treats missing as zero; `x1+x2+x3+x4+x5` propagates missing — use `SUM` for missing-aware addition

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm

The `SUM` function returns the sum of **nonmissing** arguments; if all
arguments are missing the result is missing, but a single nonmissing
argument is enough to produce a number. The `+` operator propagates
missing: `.+ 3 = .`. For row-wise accumulation across optional
variables (e.g., per-diagnosis cost buckets that may be unset),
`SUM(of ...)` is almost always what you want.

```sas
/* CORRECT - missing treated as 0; total_paid is nonmissing if any bucket is */
data claims; set claims;
  total_paid = sum(of paid_ip paid_op paid_rx);
run;
```

```sas
/* WRONG - any missing bucket poisons the total */
data claims; set claims;
  total_paid = paid_ip + paid_op + paid_rx;   /* missing if any is missing */
run;
```

### Rule 2: `ROUND(x, unit)` rounds to the nearest **multiple of unit**, not to a number of decimal places

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm

`ROUND(3.14159, 1)` returns `3`. `ROUND(3.14159, 0.01)` returns `3.14`.
The second argument is a rounding unit, not a decimal-place count —
which trips up anyone coming from `round(x, digits)` in R or
`Math.round` with scaling. For "round to N decimals" use `ROUND(x,
10**(-n))` idiomatically, i.e. `ROUND(x, 0.01)` for two decimals.

```sas
/* CORRECT - 2 decimal rounding via unit=0.01 */
data claims; set claims;
  pmpm = round(total_paid / member_months, 0.01);
run;
```

```sas
/* WRONG - unit=2 rounds to nearest even integer */
data claims; set claims;
  pmpm = round(total_paid / member_months, 2);   /* nothing like 2-decimal rounding */
run;
```

### Rule 3: `MOD(-7, 3)` returns `-1`, not `2` — SAS uses sign-of-dividend, not the mathematical modulo

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm

From the docs: "When the result is nonzero, the result has the same
sign as the first argument. The sign of the second argument is
ignored." This matches C's `%` operator, not Python's `%` or the
mathematical modulo-N that lives in [0, N). For claims work this
surfaces when computing "month-index modulo 12" with dates that land
on a negative SAS date integer, or when hashing a negative account key.
When you need the always-nonnegative version, use `mod(x, n) + n*(x<0)`
or rewrite as positive-first.

```sas
/* CORRECT - guard explicitly; never trust MOD on negatives */
data claims; set claims;
  bucket = mod(abs(acct_hash), 16);
run;
```

```sas
/* WRONG - relies on mathematical-modulo semantics; yields negative bucket */
data claims; set claims;
  bucket = mod(acct_hash, 16);   /* if acct_hash<0, bucket is negative */
run;
```

## Canonical Idioms

### Idiom: Missing-aware row total across optional claim buckets

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm

Purpose: compute a per-row total across a set of paid-amount columns
that may be missing on any given claim row. `SUM(of ...)` treats
missing as zero and returns a nonmissing total whenever at least one
input bucket is populated — the correct semantics for "total paid
across whichever service categories this claim touched."

```sas
data claims_totals; set claims;
  total_paid = sum(of paid_ip paid_op paid_rx);
run;
```

### Idiom: PMPM currency rounding to two decimals with `ROUND(x, 0.01)`

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm

Purpose: round per-member-per-month cost ratios to two decimal places
for reporting. The rounding **unit** is `0.01`, not `2` — see Rule 2.
Use `ROUND` (not `PUT(x, best12.2)`) when the downstream step arithmetic
needs the truncated value as a number, not a formatted string.

```sas
data pmpm_summary; set pmpm_raw;
  pmpm = round(total_paid / member_months, 0.01);   /* unit = 0.01 */
run;
```

### Idiom: Nonnegative-bucket hash with `ABS` guard around `MOD`

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm

Purpose: assign rows to a nonnegative bucket index for parallelized
or sharded processing. Because SAS's `MOD` takes the sign of the
dividend (Rule 3), wrap the key with `ABS()` before the modulo call —
otherwise negative keys produce negative bucket indices that break
downstream `by bucket` grouping.

```sas
data claims_bucketed; set claims;
  bucket = mod(abs(acct_hash), 16);   /* always in [0, 16) */
run;
```

## Function / Statement Quick Ref

| Name | Syntax | Purpose | Common mistake | Doc URL |
|------|--------|---------|----------------|---------|
| `SUM` | `sum(of x1-xN)` | Sum ignoring missing | Missing treated as 0 — see Rule 1 | [SUM Function](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| `MEAN` | `mean(of x1-xN)` | Row-wise mean of nonmissing | Uses nonmissing count as denominator | [MEAN Function](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| `MEDIAN` | `median(of x1-xN)` | Row-wise median | Requires all numeric args | [MEDIAN Function](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| `ROUND` | `round(x <, unit>)` | Round to nearest multiple of unit | Unit is not decimal places — see Rule 2 | [ROUND Function](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| `INT` | `int(x)` | Truncate toward 0 | Negative numbers round up, not down | [INT Function](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| `CEIL` | `ceil(x)` | Smallest integer ≥ x | Fuzzed near integers | [CEIL Function](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| `FLOOR` | `floor(x)` | Largest integer ≤ x | Fuzzed near integers | [FLOOR Function](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| `ABS` | `abs(x)` | Absolute value | Undefined on missing — returns missing | [ABS Function](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| `MOD` | `mod(x, y)` | Remainder | Sign follows dividend — see Rule 3 | [MOD Function](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| `LOG` | `log(x)` | Natural log | Not log10 — name confusion from other languages | [LOG Function](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| `EXP` | `exp(x)` | e^x | Overflow at x ≈ 709 | [EXP Function](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| `MAX` | `max(a, b, ...)` | Row-wise max of nonmissing | Different from `PROC SQL MAX(col)` aggregate | [MAX Function](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| `MIN` | `min(a, b, ...)` | Row-wise min of nonmissing | Different from `PROC SQL MIN(col)` aggregate | [MIN Function](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| `DIM` | `dim(arr <, dim-n>)` | Length of array (or nth dim) | On 2D arrays, omitting n returns first-dim length | [DIM Function](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| `HBOUND` | `hbound(arr <, n>)` | Upper bound of array index | Nonzero lower-bound arrays common in time-series work | [HBOUND Function](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| `LBOUND` | `lbound(arr <, n>)` | Lower bound of array index | Default is 1 unless explicit `array a{0:10}` | [LBOUND Function](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |

## Silent Pitfalls

All pitfalls below share the same source:
https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm

- **SUM vs `+`** — `SUM(of x1-x5)` treats missing as 0; `x1+x2+...` is
  missing if any arg is missing. Mixing the two in nested expressions
  produces surprising shape-changes on row-wise totals. See Rule 1.

- **ROUND unit vs decimal places** — `ROUND(x, 2)` rounds to the
  nearest even integer, not 2 decimals. Use `ROUND(x, 0.01)`. See
  Rule 2.

- **MOD sign-of-dividend** — `MOD(-7, 3) = -1`, not `2`. Code that
  uses `MOD` for hash-bucket assignment on signed keys will produce
  negative bucket indices. See Rule 3.

- **`MAX` / `MIN` row-wise vs column aggregate** — the DATA-step
  `MAX(a, b, c)` is row-wise across arguments; the SQL / PROC MEANS
  `MAX(col)` is column-wise across rows. The names are identical and
  the signatures are similar, so it is easy to reach for the wrong
  one in the wrong context.

## Anti-patterns (STOP signs)

**STOP** when you see any of the following — the code compiles and
produces output, but the output is almost certainly wrong:

- `a + b + c` across a set of variables that may be missing, when
  what you meant was "total of present values" → see Rule 1. Use
  `SUM(of ...)`.
- `round(x, 2)` intending 2 decimal places → see Rule 2. Use
  `round(x, 0.01)`.
- `mod(x, n)` where `x` can be negative and `bucket >= 0` is required
  → see Rule 3. Wrap with `abs()` or rewrite.

## See Also

- [functions-dates.md](functions-dates.md) — date/time functions
  (INTNX, INTCK, DATDIF) that return numeric day-counts feeding
  row-wise arithmetic here.
- [functions-strings.md](functions-strings.md) — string functions
  (SCAN, SUBSTR, COMPRESS, CATX) used alongside numeric conversions.
- [base-procs.md](base-procs.md) — `PROC MEANS` / `PROC UNIVARIATE`
  for column-wise descriptive statistics (contrast with the row-wise
  `MEAN` / `MEDIAN` functions here).
- [proc-sql.md](proc-sql.md) — SQL-context `MAX` / `MIN` / `SUM`
  aggregates (contrast with the row-wise DATA-step versions here).
- [data-step.md](data-step.md) — DATA-step statement-level reference
  (array **declaration** paired with the DIM / HBOUND / LBOUND
  inspection functions here).
- [macros.md](macros.md) — `%SYSEVALF` for floating-point arithmetic
  in macro context (contrast with integer-only `%EVAL`).
- [SAS Functions and CALL Routines: Reference](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm)
