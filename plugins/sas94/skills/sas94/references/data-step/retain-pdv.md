---
title: RETAIN accumulators and PDV initialization
loaded_when: '"retain", "PDV", accumulator, carry-forward across rows, cumulative sum, running total, "cum = cum + x", PDV-state-across-iterations, guarded predicate macro, "mf_nobs".'
---

## Critical Rules

### Rule 6: Retain accumulators and carry-forward variables — or they reset to missing each iteration

A DATA step reinitializes every non-RETAINed PDV slot to missing on each
iteration. An accumulator of the form `cum = cum + x;` therefore computes
`missing + x = missing` every row unless `cum` is retained with an
explicit initial value. The `sasjs/core` `mp_hashdataset.sas` macro
illustrates the pattern (`retain &prevkeyvar;`) when carrying state
across rows.

```sas
/* CORRECT — retain the accumulator with an explicit initial value */
data claims_running;
  set claims;
  by member_id;
  retain cum_paid 0;
  if first.member_id then cum_paid = 0;
  cum_paid = cum_paid + paid_amt;
run;
```

```sas
/* WRONG — cum_paid is not retained; every row computes missing + paid_amt = missing */
data claims_running;
  set claims;
  cum_paid = cum_paid + paid_amt;
run;
```

## Canonical Idioms

### Idiom: Guarded predicate macro for DATA-step assertions

Purpose: a one-liner test that appends PASS/FAIL rows to a shared
results dataset — lets an analyst sprinkle assertions across a long DATA
step pipeline without interrupting the flow.

```sas
/* Usage — no observations test */
%mp_assertdsobs(work.claims_clean)

/* Usage — row-count test */
%mp_assertdsobs(work.claims_clean, test=ATLEAST 1000,
  desc=claims_clean row-count sanity check)
```

### Idiom: `mf_nobs` — observation-count one-liner for open code

Purpose: quick `NLOBS` read-out via `attrn`. Useful inside `%if` gates
and PUTLOG diagnostics. The macro is a thin wrapper around
`%mf_getattrn`.

```sas
%put Number of observations=%mf_nobs(sashelp.class);
%if %mf_nobs(work.claims_clean) = 0 %then %do;
  %put WARNING- claims_clean is empty, aborting step.;
  %return;
%end;
```

## Silent Pitfalls

- **`retain` forgotten for accumulator** — `data out; set in; cum = cum + x; run;` without `retain cum 0;` — `cum` resets to missing each row, and missing + x = missing. Always `retain` accumulators with an explicit initial value.
- **Retain without BY-group reset** — an accumulator retained across
  the whole step keeps growing past group boundaries. Pair `retain`
  with `if first.group then acc = 0;`.
- **Length defaulted from first assignment** — the first assignment to
  a character variable sets its length. Declare `length name $32;` up
  front or downstream values truncate silently.

## Anti-patterns (STOP signs)

**STOP** when you see any of the following — the code compiles and
produces output, but the output is almost certainly wrong:

- `data out; set in; cum = cum + x; run;` with no `retain cum 0;` → see
  Rule 6.
- Assigning a character variable for the first time in the middle of a
  step with no prior `length` declaration; later rows truncate.

## Related

Queue-based cross-row state (different mechanism): `lag.md`. Compile vs
execute-time filtering relative to the PDV: `where-vs-if.md`.
