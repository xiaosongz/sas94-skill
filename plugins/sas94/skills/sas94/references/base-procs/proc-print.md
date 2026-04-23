---
title: PROC PRINT — NOOBS, VAR ordering
loaded_when: '"PROC PRINT", "NOOBS", "VAR statement ordering", "LABEL option on PRINT", "listing report", or "Obs column suppression".'
---

## Critical Rules

### Rule 8: `PROC PRINT VAR a b c;` orders columns; `NOOBS` drops the row-number column

Default PROC PRINT shows every variable in dataset order with a leading
`Obs` column. For inclusion in reports, restrict columns with `VAR`
(which also controls display order) and suppress the observation column
with `NOOBS`. Combine with `LABEL` to use variable labels for headers.

```sas
/* CORRECT - restricted to report columns, no Obs column, labels on */
proc print data=claims_summary noobs label;
  var member_id total_paid n_claims first_dt;
  label total_paid = 'Total Paid'
        n_claims   = 'Claim Count'
        first_dt   = 'First Claim Date';
run;
```

## Quick Ref

| Option / syntax | Purpose | Common mistake |
|-----------------|---------|----------------|
| `noobs` | Drop leading `Obs` row-number column | Leaving on → unwanted col in report |
| `label` | Use variable labels as headers | Labels missing → falls back to name |
| `var a b c;` | Control column selection and order | Omitting → every column, dataset order |
| `by g;` | Section the listing by group | Input must be sorted by `g` |
| `sumby g;` | Subtotal per BY group | Only works for numerics in `sum` |

## Anti-patterns (STOP signs)

- Default `proc print data=ds; run;` in a report output → shows every
  column (including bookkeeping vars) with an `Obs` column.
