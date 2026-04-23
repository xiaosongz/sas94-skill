---
title: Row-wise aggregate functions — SUM, MEAN, MEDIAN, MAX, MIN
loaded_when: '"SUM function", "SUM(of", "MEAN function", "MEAN(of", "MEDIAN", "row-wise MAX", "row-wise MIN", "N function", "NMISS", or any missing-aware row aggregate lookup.'
---

## Critical Rules

### Rule 1: `SUM(of x1-x5)` treats missing as zero; `x1+x2+x3+x4+x5` propagates missing — use `SUM` for missing-aware addition

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

## Canonical Idiom: Missing-aware row total across optional claim buckets

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

## Quick Ref

| Name | Syntax | Purpose | Common mistake |
|------|--------|---------|----------------|
| `SUM` | `sum(of x1-xN)` | Sum ignoring missing | Missing treated as 0 — see Rule 1 |
| `MEAN` | `mean(of x1-xN)` | Row-wise mean of nonmissing | Uses nonmissing count as denominator |
| `MEDIAN` | `median(of x1-xN)` | Row-wise median | Requires all numeric args |
| `MAX` | `max(a, b, ...)` | Row-wise max of nonmissing | Different from `PROC SQL MAX(col)` aggregate |
| `MIN` | `min(a, b, ...)` | Row-wise min of nonmissing | Different from `PROC SQL MIN(col)` aggregate |

## Silent Pitfalls

- **SUM vs `+`** — `SUM(of x1-x5)` treats missing as 0; `x1+x2+...` is
  missing if any arg is missing. Mixing the two in nested expressions
  produces surprising shape-changes on row-wise totals. See Rule 1.

- **`MAX` / `MIN` row-wise vs column aggregate** — the DATA-step
  `MAX(a, b, c)` is row-wise across arguments; the SQL / PROC MEANS
  `MAX(col)` is column-wise across rows. The names are identical and
  the signatures are similar, so it is easy to reach for the wrong
  one in the wrong context. For the column-wise variant, see
  `../base-procs/proc-means.md` and `../proc-sql/joins.md`.

- **`MEAN` denominator is nonmissing count** — `MEAN(of x1-x5)` divides
  by however many of the five slots were nonmissing, which silently
  inflates per-member averages when you expected divide-by-5.

## Anti-patterns (STOP signs)

**STOP** when you see any of the following — the code compiles and
produces output, but the output is almost certainly wrong:

- `a + b + c` across a set of variables that may be missing, when
  what you meant was "total of present values" → see Rule 1. Use
  `SUM(of ...)`.
- `max(col)` / `min(col)` inside a DATA step expecting a
  column-wise aggregate — DATA step `MAX` / `MIN` are row-wise.
  Use `PROC MEANS` or `PROC SQL` for the column aggregate.
