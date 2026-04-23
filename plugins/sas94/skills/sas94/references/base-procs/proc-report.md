---
title: PROC REPORT — DEFINE type; NOWD/NOWINDOWS alias
loaded_when: '"PROC REPORT", "DEFINE", "DISPLAY ANALYSIS GROUP ORDER", "NOWD", "NOWINDOWS", "COLUMN statement", "COMPUTE block", or "grouped formatted report".'
---

## Critical Rules

### Rule 6: `PROC REPORT DEFINE` type determines aggregation — `DISPLAY` / `ANALYSIS` / `GROUP` / `ORDER` are not interchangeable

`DISPLAY` shows row-level values; `ANALYSIS` computes an aggregation
(`sum`, `mean`, etc. via the trailing keyword); `GROUP` collapses
rows with equal values into one; `ORDER` sorts without collapsing.
A common bug: declaring a key column as `DISPLAY` when you meant
`GROUP` — the report shows duplicate-key rows instead of summarizing.

(`NOWD` and `NOWINDOWS` are interchangeable aliases for the same option
— batch-mode execution, no interactive REPORT window. SAS 9.4 docs use
`NOWINDOWS` as the canonical spelling; legacy code uses `NOWD`.)

```sas
/* CORRECT - member_id is the grouping; paid_amt is the analysis */
proc report data=claims nowd;
  column member_id paid_amt n_claims;
  define member_id / group 'Member ID';
  define paid_amt  / analysis sum format=dollar12.2 'Total Paid';
  define n_claims  / analysis n 'Claim Count';
run;
```

```sas
/* WRONG - DISPLAY keeps every row; report has one row per claim, not per member */
proc report data=claims nowd;
  column member_id paid_amt;
  define member_id / display;
  define paid_amt  / display;
run;
```

## Quick Ref

| DEFINE type | Behavior | Use when |
|-------------|----------|----------|
| `display` | One row per input obs, raw value | Detail listing, no collapse |
| `analysis <stat>` | Aggregated via `sum` / `mean` / `n` / etc. | Need totals / averages |
| `group` | Collapse equal-valued rows into one | Summary key column |
| `order` | Sort without collapsing | Ordered detail listing |
| `across` | Values become column headers | Cross-tab-style layout |
| `computed` | Derived value (in `compute` block) | Calculated column |

## Anti-patterns (STOP signs)

- `proc report; define key / display; ...` when summarization was
  intended → output has one row per detail, not per key. Use
  `define key / group`.

Cross-ref: for routing PROC REPORT output to Excel/RTF/PDF see the
ODS reference.
