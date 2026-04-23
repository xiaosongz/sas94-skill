---
title: PROC SQL CASE expressions
loaded_when: '"CASE WHEN", "searched CASE", "simple CASE", "derived column", "bucket / classify inline", "ELSE catch-all", conditional-column creation in a SELECT list.'
---

## Critical Rules

### Rule: Use the searched form (`CASE WHEN cond THEN ...`) for anything that isn't strict equality

The simple form `CASE col WHEN value THEN ...` compares `col` for
equality against each `WHEN` literal — no comparison operators
(`<`, `>`, `between`), no compound predicates. The searched form
(`CASE WHEN <predicate> THEN ...`) is the general case and always
safe to use.

```sas
/* CORRECT - searched form handles range / compound predicates */
proc sql;
  create table claims_tagged as
  select member_id,
         service_dt,
         paid_amt,
         case
           when paid_amt = 0            then 'zero-pay'
           when paid_amt < 100          then 'low'
           when paid_amt < 1000         then 'mid'
           else                              'high'
         end as amt_bucket
  from claims;
quit;
```

```sas
/* WRONG - simple form does not accept comparison operators */
proc sql;
  create table claims_tagged as
  select member_id,
         case paid_amt
           when 0          then 'zero-pay'
           when < 100      then 'low'    /* syntax error */
         end as amt_bucket
  from claims;
quit;
```

### Rule: Always include an explicit `ELSE` — a missing `ELSE` yields missing values silently

When no `WHEN` predicate matches and there is no `ELSE`, the result is
a SAS missing value (`.` for numeric, `' '` for character). This is
rarely what the author intended; downstream `IF`, PROC FREQ counts,
and joins on the derived column all behave differently than expected.

```sas
/* CORRECT - ELSE catches everything not matched above */
proc sql;
  select member_id,
         case
           when age < 18   then 'child'
           when age < 65   then 'adult'
           when age >= 65  then 'senior'
           else                 'unknown'   /* explicit catch-all */
         end as age_band
  from members;
quit;
```

## Canonical Idiom: CASE for row-level conditional classification

Compute a derived category column inline — cleaner than a secondary
DATA step and keeps the logic next to the SELECT that uses it.

```sas
proc sql;
  create table claims_tagged as
  select member_id,
         service_dt,
         paid_amt,
         case
           when paid_amt = 0            then 'zero-pay'
           when paid_amt < 100          then 'low'
           when paid_amt < 1000         then 'mid'
           else                              'high'
         end as amt_bucket
  from claims;
quit;
```

## Simple vs searched form

| Form | Syntax | When to use |
|------|--------|-------------|
| Simple | `case col when v1 then ... when v2 then ... else ... end` | Pure equality buckets on a single column (think lookup table) |
| Searched | `case when <predicate> then ... when <predicate> then ... else ... end` | Anything with `<`, `>`, `between`, compound logic, or multi-column predicates |

Searched form is always safe to use where simple form would work, so
when in doubt, write the searched form.

## Quick Ref

| Name | Syntax | Purpose | Common mistake |
|------|--------|---------|----------------|
| `CASE` (searched) | `case when cond then val else val end as name` | Row-level conditional | Missing `ELSE` → rows get missing value silently |
| `CASE` (simple) | `case col when v then val else val end as name` | Equality-only bucket on one column | Using a comparison operator in a `WHEN` literal slot |

## Silent Pitfalls

- **Missing `ELSE` → silent missing value** — every unmatched row gets
  `.` / `' '`; PROC FREQ on the derived column then shows a silent
  "missing" bucket instead of surfacing the unmatched predicates.
- **Simple-form `WHEN`-literal list is positional equality only** —
  `when < 100 then ...` is a syntax error, and `when 0, 100 then ...`
  compares against each literal, not a range.
- **Character-length inference** — the created column's length comes
  from the first `THEN` value; later longer values get truncated.
  Cast the longest form first or wrap every branch with
  `put(value, $10.)`.

## Anti-patterns

- Chained `IFN() / IFC()` nesting where a searched `CASE` would be
  flatter and readable.
- `CASE` without `ELSE` in a reference-table lookup — silent missing
  is almost always a latent bug.
- Simple-form `CASE` with a single comparison hidden inside a
  function call (`case sign(x) when 1 then ...`) — readable, but a
  searched form is usually clearer.
