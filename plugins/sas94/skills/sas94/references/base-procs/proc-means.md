---
title: PROC MEANS — NOPRINT + OUTPUT OUT= idiom
loaded_when: '"PROC MEANS", "PROC SUMMARY", "class-level summary", "OUTPUT OUT=", "_TYPE_", "_FREQ_", "NOPRINT", "sum mean n median by group", or "roll-up aggregation".'
---

## Critical Rules

### Rule 2: `PROC MEANS` prints by default — use `NOPRINT` when you only want `OUTPUT OUT=`

A bare `proc means data=claims; ... output out=summary ... ; run;` writes
the OUTPUT dataset AND pollutes the `.lst` / ODS destination with the
default print. In batch or long pipelines this is minor; in generated
QA reports it is an unwanted section. Add `NOPRINT` on the PROC MEANS
statement.

```sas
/* CORRECT - OUTPUT dataset only, no printed table */
proc means data=claims noprint;
  class member_id;
  var paid_amt;
  output out=claims_by_member(drop=_type_ _freq_)
    sum=total_paid n=n_claims;
run;
```

```sas
/* WRONG - produces both the dataset AND a printed table */
proc means data=claims;
  class member_id;
  var paid_amt;
  output out=claims_by_member sum=total_paid n=n_claims;
run;
```

## Canonical Idiom: CLASS-level summary → flat output dataset

Purpose: roll up `paid_amt` and `days_supply` per `member_id`, drop
the `_TYPE_` / `_FREQ_` bookkeeping columns, name output stats
explicitly. This is the single most common Base-SAS summarization
pattern in claims work.

```sas
proc means data=claims noprint;
  class member_id;
  var paid_amt days_supply;
  output out=claims_by_member(drop=_type_ _freq_)
    sum(paid_amt)    = total_paid
    sum(days_supply) = total_days
    n(paid_amt)      = n_claims;
run;
```

## Quick Ref

| Option / syntax | Purpose | Common mistake |
|-----------------|---------|----------------|
| `noprint` | Suppress default printed table | Forgetting → pollutes listing |
| `class g;` | Group rows without requiring sort | Confusing with `by` (needs sort) |
| `var x y;` | Columns to summarize | Omitting → every numeric gets summarized |
| `output out=ds sum()= mean()= ;` | Named output stats | Forgetting to drop `_TYPE_` / `_FREQ_` |
| `output out=ds(drop=_type_ _freq_)` | Strip bookkeeping cols | Leaves `_TYPE_=0` all-class row if not filtered |

## Anti-patterns (STOP signs)

- `proc means; class g; var x; output out=ds sum=; run;` with no
  `NOPRINT` → unintended printed table.

Cross-ref: for SQL `GROUP BY` as an alternative, see the PROC SQL
reference.
