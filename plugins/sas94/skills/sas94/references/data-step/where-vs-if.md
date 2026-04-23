---
title: WHERE vs subsetting IF
loaded_when: '"WHERE", "subsetting IF", filter on a derived column, "Variable X is not on file", compile-time vs execute-time filtering, index-aware pushdown.'
---

## Critical Rules

### Rule 7: `WHERE` filters pre-PDV (compile time) — cannot see derived variables; use subsetting `IF` for those

`WHERE` is evaluated against the **input dataset** before the row is
loaded into the PDV. This makes it fast (filter pushed down to the I/O
layer, index-aware) but means `WHERE` cannot reference any variable
created inside the DATA step — attempting to do so produces
`ERROR: Variable X is not on file ...`. Subsetting `IF` is evaluated
**after** the assignment statements on each iteration, so it sees
derived variables, but pays for reading the row first. Rule of thumb:
`WHERE` for raw input columns, `IF` for anything computed.

```sas
/* CORRECT — WHERE filters raw input cols; IF filters on a derived col */
data claims_2024;
  set raw.claims;
  where paid_amt > 0                            /* raw column — WHERE ok */
    and service_dt >= '01JAN2024'd;
  svc_yr = year(service_dt);                    /* derived in DATA step */
  if svc_yr = 2024 and paid_amt > 10000;        /* subsetting IF on derived */
run;
```

```sas
/* WRONG — WHERE references svc_yr before it exists on the input */
data claims_2024;
  set raw.claims;
  svc_yr = year(service_dt);
  where svc_yr = 2024;                          /* ERROR: Variable SVC_YR is not on file RAW.CLAIMS. */
run;
```

## Silent Pitfalls

- **`WHERE` on a derived variable** — `where` is compile-time and
  operates on the input, so it cannot see a column created later in
  the DATA step. Use subsetting `IF` for derived columns. The error
  (`Variable X is not on file ...`) is loud at compile time, but the
  misuse *inside* macro-generated code can be hidden in the macro log.
- **`WHERE` expressions on character columns with trailing blanks** —
  `where name = 'Jo';` ignores trailing blanks only in exact-equality
  compares on fixed-length char columns. Mixing `where` and `if` on
  the same character predicate can produce divergent row counts.

## Anti-patterns (STOP signs)

**STOP** when you see any of the following — the code compiles and
produces output, but the output is almost certainly wrong:

- `where derived_var = ...;` after assigning `derived_var` in the step →
  see Rule 7. ERROR at compile time; use subsetting `IF`.
- Relying on `_N_` as a row number after a `where` — `_N_` counts PDV
  iterations, which skip `where`-excluded rows entirely; the input-row
  ordinal is not recoverable from `_N_`.

## Related

For PDV state that persists across iterations (retained accumulators):
`retain-pdv.md`. For queue-based previous-row lookup that *is* available
to subsetting IF but not to WHERE: `lag.md`.
