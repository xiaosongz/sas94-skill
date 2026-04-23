---
title: INTNX and INTCK interval functions
loaded_when: '"INTNX", "INTCK", "interval shift", "interval count", "alignment", "same-day", "month boundary", "anniversary", "count months between", or any interval-arithmetic lookup.'
---

## Critical Rules

### Rule 1: `INTNX('interval', dt, 0)` with no `alignment` returns the **beginning** of the interval, not `dt` — use `'S'` (SAME) for same-day alignment

The fourth argument `alignment` defaults to `BEGINNING`. So
`intnx('month', service_dt, 0)` returns the first of `service_dt`'s
month, not `service_dt` itself. Concrete example:
`intnx('month', '15MAR2024'd, 0)` returns `'01MAR2024'd` — the 15th
silently becomes the 1st because the default alignment is
`BEGINNING`. For "shift by N months but keep the day-of-month"
semantics use `'SAME'` (alias `'S'`). A common claims bug: computing
`months_since_start = intck('month', a, b)` and then trying to
reconstruct the corresponding date with `intnx('month', a, k)` —
which lands on the first of each month, not the anniversary day.

```sas
/* CORRECT - SAME alignment preserves day-of-month */
data claims; set claims;
  anniversary = intnx('year', enroll_dt, 1, 'same');
run;
```

```sas
/* WRONG - default BEGINNING alignment; lands on 01JAN */
data claims; set claims;
  anniversary = intnx('year', enroll_dt, 1);   /* not what the name suggests */
  /* e.g. intnx('month', '15MAR2024'd, 0) = '01MAR2024'd -- default alignment='BEGINNING' */
run;
```

## Canonical Idiom: Month-end alignment for claims billing cycles

Purpose: map every service date to the end of its calendar month for
PMPM / member-month aggregation. Use `INTNX` with `'E'` (END)
alignment — the last-day-of-month adjustment handles February and
leap years automatically, so there's no special case for 30- vs
31-day months.

```sas
data claims_eom; set claims;
  bill_eom   = intnx('month', service_dt, 0, 'e');   /* E = end-of-month */
  bill_start = intnx('month', service_dt, 0, 'b');   /* B = start-of-month */
run;
```

## Quick Ref

| Name | Syntax | Purpose | Common mistake |
|------|--------|---------|----------------|
| `INTCK` | `intck('interval', d1, d2 <, 'method'>)` | Count interval boundaries between two dates | Default `method='DISCRETE'` counts boundaries; use `'CONTINUOUS'` for anniversary semantics |
| `INTNX` | `intnx('interval', d, n <, 'align'>)` | Shift date by N intervals | Default align=`'BEGINNING'`; use `'S'` for same-day (see Rule 1) |

Alignment values: `'B'` (BEGINNING, default), `'E'` (END), `'M'` (MIDDLE), `'S'` (SAME — preserves day-of-month).

`INTCK` counts boundary crossings, not elapsed duration. Between
`01JAN2024` and `31JAN2024` the DISCRETE month count is `0` (no
boundary crossed); between `31JAN2024` and `01FEB2024` it is `1` (one
boundary) even though only one day elapsed. Use `'CONTINUOUS'` as the
method argument when you want anniversary-style "has a full interval
elapsed" semantics.

## Silent Pitfalls

- **INTNX default alignment is `BEGINNING`** — `intnx('month', dt, 0)`
  is the first of the month, not `dt`. Every `INTNX` call in a claims
  pipeline should carry an explicit alignment argument. See Rule 1.
- **INTCK counts boundaries, not duration** — `intck('month', a, b)`
  measures month-boundary crossings. Two dates one day apart can
  return `1` if they straddle a month boundary; two dates 29 days
  apart in the same month return `0`. Use `'CONTINUOUS'` for
  anniversary-style counting.
- **Reconstructing a date from an INTCK count** — computing
  `k = intck('month', a, b)` and then `intnx('month', a, k)` lands on
  the first of each month, not the anniversary day, because of the
  default alignment. Pair with `'SAME'`.

## Anti-patterns

- `intnx('month', d, n)` with no fourth argument when you meant
  "same-day n months later" → see Rule 1.
- `intck('month', a, b)` treated as "number of months between" — it
  is a boundary count, not a duration. Cross-check against a
  hand-computed anniversary or use `'CONTINUOUS'`.
- Round-tripping `a → intck → intnx` without an explicit `'same'`
  alignment — the reconstructed date silently collapses to the first
  of each month.

See `date-arithmetic.md` for day-subtraction and "add one month"
patterns; see `construction.md` for building the input dates.
