---
title: PROC GLM rules
loaded_when: PROC GLM, ANOVA / ANCOVA / linear regression, LSMEANS, Type III SS, CONTRAST / ESTIMATE, or when a fixed-effects linear model is needed without random effects.
---

## Critical Rules

### Rule 1: `CLASS` is required for every categorical predictor — a numeric categorical in `MODEL` without `CLASS` is silently treated as continuous

GLM (together with LOGISTIC, MIXED, GENMOD) accepts a `CLASS`
statement that names the categorical predictors. Any predictor
listed in `MODEL` but not in `CLASS` is treated as continuous — a
classic claims-data bug where `sex` coded as 1/2 or `region` coded
1–4 yields a "one-unit increase" coefficient rather than the
intended contrast. The procedure runs silently.

```sas
/* CORRECT - treatment and region declared in CLASS */
proc glm data=trial;
  class treatment region;
  model outcome = treatment region age baseline / solution ss3;
  lsmeans treatment / diff cl;
run;
quit;
```

```sas
/* WRONG - treatment coded 1/2/3 numeric; treated as continuous dose */
proc glm data=trial;
  model outcome = treatment region age;
run;
quit;
```

### Rule 2: `LSMEANS` in GLM produces covariate-adjusted (marginal) means — NOT arithmetic means

`lsmeans class-effect;` computes the least-squares means — the
predicted value at a common set of covariate values, effectively the
"adjusted" mean holding other model covariates at their mean / first
level. It is NOT the simple arithmetic mean per group; that is what
`proc means; class g; var x;` gives you. Reporting LSMEANS as "group
means" or `PROC MEANS` output as "adjusted means" is a common
write-up error. Use the right one for the question: raw descriptive
→ `PROC MEANS`; marginal (adjusted for model covariates) → `LSMEANS`.

```sas
/* CORRECT - LSMEANS gives the covariate-adjusted mean per treatment */
proc glm data=trial;
  class treatment center;
  model outcome = treatment center age baseline / solution;
  lsmeans treatment / diff cl;
run;
quit;
```

```sas
/* WRONG - reporting PROC MEANS arithmetic means and calling them
   "adjusted for age and baseline" when they are not. */
proc means data=trial mean stderr;
  class treatment;
  var outcome;
run;
/* no adjustment has happened - any "adjusted" claim is false */
```

## Canonical Idioms

### Idiom: ANCOVA with covariate-adjusted treatment means

Purpose: compare treatment means adjusted for baseline covariates —
the standard ANCOVA report. `CLASS` declares the factors; `SOLUTION`
on `MODEL` prints parameter estimates; `LSMEANS treatment / diff cl`
gives pairwise adjusted contrasts with confidence limits.

```sas
ods output ParameterEstimates=glm_pe LSMeans=glm_lsm Diff=glm_diff;
proc glm data=trial;
  class treatment center;
  model outcome = treatment center age baseline / solution ss3;
  lsmeans treatment / diff cl;
  estimate 'A vs B' treatment 1 -1 0;
run;
quit;
ods output close;
```

## Quick Ref

| Name | Syntax | Purpose | Common mistake |
|------|--------|---------|----------------|
| `PROC GLM` | `proc glm; class g; model y = g x;` | ANOVA / ANCOVA / linear regression | Treating a fit as MIXED when data are clustered |
| `CLASS` (GLM) | `class treatment center;` | Declare categorical predictors | Numeric categorical missing from CLASS → continuous |
| `MODEL ... / SOLUTION` | `model y = x / solution ss3;` | Print parameter estimates | Omitting — then no coefficient table prints |
| `LSMEANS` | `lsmeans trt / diff cl;` | Covariate-adjusted marginal means | Treating as raw group means (Rule 2) |
| `CONTRAST` / `ESTIMATE` | `estimate 'A vs B' trt 1 -1 0;` | Custom linear contrasts | Wrong coefficient order across CLASS levels |
| `ODS OUTPUT` | `ods output LSMeans=lsm Diff=diff;` | Capture adjusted means / contrasts | Wrong table name → empty dataset |

## Silent Pitfalls

- **Numeric categorical as continuous** — any categorical predictor
  coded numerically (treatment=1/2/3, region=1..4) that is omitted
  from `CLASS` is silently modeled as continuous. See Rule 1.
- **Reporting `MEANS` output as "adjusted"** — `PROC MEANS` produces
  arithmetic means, not covariate-adjusted (LS) means. Labeling them
  "adjusted" in a report is a write-up error. See Rule 2.
- **Using GLM when data are clustered** — if observations are nested
  within patients / centers and you care about the variance
  components, GLM underestimates SEs. Move to `PROC MIXED`.

## Anti-patterns

- `proc glm; model y = treatment; run;` with `treatment` numeric
  1/2/3 and no `CLASS` → silent continuous fit.
- Reporting `PROC MEANS` output as "covariate-adjusted" → see Rule 2.
  LSMEANS gives adjusted; MEANS does not.
- Fitting GLM to clustered / repeated-measures data and reporting
  the SEs as-is → use MIXED (see `proc-mixed.md`).
