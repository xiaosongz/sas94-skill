---
title: PROC UNIVARIATE — NOPRINT extraction
loaded_when: '"PROC UNIVARIATE", "quantiles", "percentiles", "p25 p50 p75 p95 p99", "median", "extreme observations", "distribution moments", "normality tests", or "OUTPUT OUT= quantile extraction".'
---

## Critical Rules

### Rule 7: `PROC UNIVARIATE` produces a long default report — use `NOPRINT` + `OUTPUT OUT=` for extraction pipelines

A bare `proc univariate` prints moments, location / variability, extreme
observations, missing-value counts, and plots for every numeric variable
listed in `VAR` — pages of output in a batch. For pipeline extraction
use `NOPRINT` and pull out named statistics via `OUTPUT OUT=`.

```sas
/* CORRECT - quiet extraction of specific statistics */
proc univariate data=claims noprint;
  var paid_amt;
  output out=paid_stats
    n=n mean=mean median=p50 q1=p25 q3=p75 p95=p95 p99=p99 max=max;
run;
```

```sas
/* WRONG - floods the output destination with every default panel */
proc univariate data=claims;
  var paid_amt;
run;
```

## Quick Ref

| Option / keyword | Purpose | Common mistake |
|------------------|---------|----------------|
| `noprint` | Suppress all default panels | Forgetting → pages of output per var |
| `var x;` | Variables to summarize | Omitting → every numeric panel printed |
| `output out=ds p25= p50= p75=` | Named quantile stats | Using `pctlpts=` without `pctlpre=` |
| `pctlpts=90 95 99 / pctlpre=p_` | Custom percentiles | Forgetting `pctlpre=` → suffix-name clash |
| `histogram / normal;` | Goodness-of-fit | Requires non-`noprint`; separate ODS output |

## Anti-patterns (STOP signs)

- Bare `proc univariate; var x; run;` inside a batch pipeline →
  floods the listing; use `noprint` + `output out=`.

Cross-ref: for normality testing / distribution-fit plots see the
stat-procs reference; for routing the report to Excel/RTF see the
ODS reference.
