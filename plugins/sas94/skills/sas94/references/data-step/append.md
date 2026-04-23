---
title: PROC APPEND shape rules
loaded_when: '"PROC APPEND", appending, stacking datasets, "FORCE", BASE vs DATA column mismatch, schema-drift append.'
---

## Critical Rules

### Rule 3: PROC APPEND variable-shape rules — missing-from-BASE ERRORs, missing-from-DATA silently nulls (GWU §3)

`PROC APPEND BASE=a DATA=b` uses BASE's variable definitions. Without
`FORCE`, any variable in DATA= that is absent from BASE= causes the step
to **fail with ERROR** — nothing is appended. With `FORCE`, the extra
variable is **dropped with a WARNING**. The silent mode is different:
when BASE= carries a variable absent from DATA=, appended rows get
missing values in that column, with no diagnostic — easy to miss when
BASE= has been recently extended.

```sas
/* CORRECT — explicitly reshape DATA to match BASE before appending */
data claims_new_aligned;
  set claims_new;
  keep member_id service_dt paid_amt dx_code;   /* whatever BASE=claims has */
run;
proc append base=claims data=claims_new_aligned;   /* no FORCE needed */
run;

/* or: use FORCE only when knowingly dropping new columns */
proc append base=claims data=claims_new force;     /* drops new-in-DATA vars w/ WARNING */
run;
```

```sas
/* WRONG — DATA has a column absent from BASE; step errors without FORCE */
proc append base=claims data=claims_new;
run;
/* ERROR: Variable ndc_code in DATA set not in BASE set. No appending done. */

/* Subtler silent mode: BASE has a column absent from DATA */
proc append base=claims_v2 data=claims_v1;   /* v2 added ndc_code; v1 lacks it */
run;
/* Step succeeds; ndc_code is missing for every v1 row — no WARNING. */
```

## Silent Pitfalls

- **PROC APPEND mismatched-shape modes** — without `FORCE`, a column in
  DATA= absent from BASE= ERRORs (step fails, nothing appended); with
  `FORCE` the extra column drops with a WARNING. The silent mode is
  BASE-has-extra: appended rows get missing values in that column, no
  diagnostic.
- **Type / length mismatch under FORCE** — `FORCE` also silently
  truncates character columns when BASE's length is shorter than DATA's.
  Align `LENGTH` explicitly before appending.

## Anti-patterns (STOP signs)

**STOP** when you see any of the following — the code compiles and
produces output, but the output is almost certainly wrong:

- `proc append base=a data=b;` where `b` has a column not in `a`, no
  `FORCE` specified → step ERRORs, nothing appended; see Rule 3 / GWU §3.
- `proc append base=a data=b force;` across a schema-drift boundary
  without a row-count assertion afterwards — dropped columns go unnoticed.

## Related

For schema-aware stacking, a SET-based DATA step with explicit `length` /
`keep` is usually safer than `PROC APPEND FORCE`: see `retain-pdv.md`
for the PDV-init pattern and `merge.md` for multi-dataset read semantics.
