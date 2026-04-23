---
title: ODS OUTPUT capture pattern
loaded_when: '"ODS OUTPUT", "capture proc table as dataset", "ParameterEstimates dataset", "FitStatistics dataset", "OddsRatios dataset", "ods trace", "empty dataset from proc", "0-row ods output", or any task that converts a named PROC output object into a SAS dataset.'
---

## Critical Rules

### Rule: `ODS OUTPUT Table=ds;` requires the exact ODS table name — discover it with `ODS TRACE ON;`

`ODS OUTPUT ParameterEstimates=pe;` captures the proc's named
output object as a SAS dataset. Mis-type the table name and you
get a silently empty dataset — no error, no warning, just zero
rows. Run the proc once under `ods trace on;` to print every
object's path and label to the log, then match the name exactly
(case-insensitive, but spelling must match). `ODS TRACE OFF;`
afterward to stop flooding the log.

```sas
/* CORRECT - discover the table name, then capture it */
ods trace on;
proc logistic data=claims; model outcome = age sex; run;
ods trace off;
/* log shows Name: ParameterEstimates, Name: FitStatistics, etc. */

ods output ParameterEstimates=lr_pe
           FitStatistics=lr_fit;
proc logistic data=claims; model outcome = age sex; run;
```

```sas
/* WRONG - misspelled name silently produces zero rows in lr_pe */
ods output ParamEstimates=lr_pe;
proc logistic data=claims; model outcome = age sex; run;
/* lr_pe exists but has 0 observations; no message about the miss */
```

### Rule: Set `options replace=yes;` when `ODS OUTPUT Table=ds;` targets an existing dataset name

The ODS OUTPUT statement documentation flags this explicitly: to
ensure the captured dataset is replaced on re-runs rather than
triggering an error, set `options replace=yes;` (which is the
default on most installs, but not all). When `REPLACE=NO` is
active — often the case in shops with tight data-loss policies —
re-running a script that writes `ODS OUTPUT PE=lr_pe;` errors on
the second run because `lr_pe` already exists.

```sas
/* CORRECT - replace is on; dataset overwrites cleanly on re-run */
options replace=yes;
ods output ParameterEstimates=lr_pe;
proc logistic data=claims; model outcome = age sex; run;
```

```sas
/* WRONG - in a REPLACE=NO session the second run errors out */
ods output ParameterEstimates=lr_pe;
proc logistic data=claims; model outcome = age sex; run;
/* rerun => "File WORK.LR_PE already exists and REPLACE=NO" */
```

## Canonical Idioms

### Capture PROC LOGISTIC parameter estimates as a downstream-usable dataset

The most common ODS OUTPUT pattern in modeling pipelines — pull
the ParameterEstimates and FitStatistics tables out as SAS
datasets for merging into a results-summary table or forest-plot
input. `ods trace on` is how you discover the exact names; after
the first run, pin them in code.

```sas
ods output ParameterEstimates=lr_pe
           FitStatistics=lr_fit
           OddsRatios=lr_or;
proc logistic data=claims;
  class plan_type(ref='HMO') / param=ref;
  model outcome(event='1') = age sex plan_type;
run;
/* lr_pe has Variable, Estimate, StdErr, WaldChiSq, ProbChiSq */
```

### Discover table names with `ODS TRACE ON;` before writing `ODS OUTPUT`

The "what do I call this thing" discovery workflow. Run the proc
once with trace on, scan the log for output-object names, then
hardcode them into `ODS OUTPUT`. Essential for less-used procs
(NLMIXED, GLIMMIX) where the table inventory isn't memorized.

```sas
ods trace on / label;
proc glimmix data=claims;
  class plan_type;
  model paid_amt = age plan_type / dist=gamma link=log;
  random intercept / subject=site;
run;
ods trace off;
/* log prints: Name: ParameterEstimates, Label: "Solutions for Fixed Effects"
   Name: FitStatistics, Label: "Fit Statistics"
   Name: CovParms, Label: "Covariance Parameter Estimates" ... */
```

## Quick Ref

| Name | Syntax | Purpose | Common mistake |
|------|--------|---------|----------------|
| `ODS OUTPUT` | `ods output Table=ds Table2=ds2;` | Capture output objects as SAS datasets | Mis-typed table name → silent 0-row dataset |
| `ODS TRACE ON` | `ods trace on / label;` | Log every output object's path + label | Leaving on → log floods with trace records |
| `ODS TRACE OFF` | `ods trace off;` | Stop tracing | Forgetting, then log fills with object records |
| `options replace=yes` | `options replace=yes;` | Allow ODS OUTPUT target dataset to overwrite | Running under `REPLACE=NO` → second run errors |

## Silent Pitfalls

- **`ODS OUTPUT` table-name typo** — no error, no warning, just a
  silently empty dataset. Discover correct names via `ODS TRACE ON;`.
- **`REPLACE=NO` session re-run failure** — `ODS OUTPUT Table=ds;`
  errors on the second run if `ds` exists and `REPLACE=NO`.
- **Trace left on** — forgetting `ODS TRACE OFF;` floods the log
  with object-path records for every subsequent PROC.

## Anti-patterns

- `ODS OUTPUT ParamEstimates=...;` (misspelled) → silent zero-row
  capture. Run `ODS TRACE ON;` once to confirm the exact name.
- Relying on unknown `REPLACE=` session state in production — set
  `options replace=yes;` explicitly at the top of the script.

For modeling-specific capture targets see `../stat-procs/<proc>.md`. For the alternative of suppressing printed output while keeping a dataset, see `../base-procs/<proc>.md` (`NOPRINT` option).
