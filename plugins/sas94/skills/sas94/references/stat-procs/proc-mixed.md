---
title: PROC MIXED rules
loaded_when: PROC MIXED, linear mixed models, random intercepts / slopes, repeated-measures covariance (AR(1), CS, UN), SUBJECT= / TYPE= / ddfm, REML.
---

## Critical Rules

### Rule 1: `CLASS` is required for every categorical predictor — a numeric categorical in `MODEL` without `CLASS` is silently treated as continuous

MIXED (together with LOGISTIC, GLM, GENMOD) accepts a `CLASS`
statement that names the categorical predictors. Any predictor
listed in `MODEL` but not in `CLASS` is treated as continuous. In
MIXED this also applies to `SUBJECT=` — subject IDs must be in
`CLASS` or the partitioning into subject-level blocks is wrong.

```sas
/* CORRECT - pat_id, region, treatment all in CLASS */
proc mixed data=panel;
  class pat_id region treatment;
  model cost = age treatment region / ddfm=kr solution;
  random intercept / subject=pat_id;
run;
```

```sas
/* WRONG - pat_id omitted from CLASS; subject blocking silently broken */
proc mixed data=panel;
  class region treatment;
  model cost = age treatment region / ddfm=kr;
  random intercept / subject=pat_id;
run;
```

### Rule 4: MIXED `REPEATED` models R-side (within-subject residual correlation); `RANDOM` models G-side (random effects) — they are NOT interchangeable

Per the MIXED Procedure docs, `RANDOM` specifies random-effects
parameters (the `Z` design matrix and `G` covariance), and
`REPEATED` specifies covariance structures for repeated measures on
subjects (the `R` covariance). Using `RANDOM` to try to model a
residual AR(1) within subjects, or `REPEATED` to try to fit a random
intercept, is a silent misspecification — the model fits, but the
variance decomposition does not mean what the analyst intended.
Pick based on what you are modelling: shared-baseline clustering →
`RANDOM`; within-subject serial correlation in residuals →
`REPEATED`.

```sas
/* CORRECT - random intercept per patient (G-side) */
proc mixed data=panel;
  class pat_id region;
  model cost = age treatment region / ddfm=kr;
  random intercept / subject=pat_id;
run;
```

```sas
/* CORRECT - AR(1) residual correlation within patient-visits (R-side) */
proc mixed data=longitudinal;
  class pat_id visit region;
  model cost = age treatment region visit;
  repeated visit / subject=pat_id type=ar(1);
run;
```

```sas
/* WRONG - RANDOM statement used to try to model within-subject AR(1);
   fits without error but the variance structure is not AR(1). */
proc mixed data=longitudinal;
  class pat_id visit region;
  model cost = age treatment region visit;
  random visit / subject=pat_id type=ar(1);
run;
```

### Rule 8: `LSMEANS` in MIXED produces covariate-adjusted (marginal) means — NOT arithmetic means

`lsmeans class-effect;` computes the least-squares means — the
predicted value at a common set of covariate values. It is NOT the
simple arithmetic mean per group; that is what `proc means; class
g; var x;` gives you. Use raw descriptive → `PROC MEANS`; marginal
(adjusted for model covariates) → `LSMEANS`.

```sas
/* CORRECT - LSMEANS gives the covariate-adjusted mean per treatment */
proc mixed data=trial;
  class treatment center;
  model outcome = treatment center age baseline;
  lsmeans treatment / diff cl;
run;
```

## Canonical Idioms

### Idiom: Mixed model for panel claims with random patient intercept

Purpose: model longitudinal claims cost across patients with a
random intercept per patient (captures the patient-level clustering)
and Kenward-Roger denominator degrees of freedom (standard for
unbalanced panels). CLASS on both `pat_id` and categorical fixed
effects; `random intercept / subject=pat_id` specifies the G-side
variance component.

```sas
proc mixed data=panel;
  class pat_id region treatment;
  model cost = age treatment region / ddfm=kr solution;
  random intercept / subject=pat_id;
  lsmeans treatment / diff cl;
run;
```

## Quick Ref

| Name | Syntax | Purpose | Common mistake |
|------|--------|---------|----------------|
| `PROC MIXED` | `proc mixed; class g; model y = x; random intercept / subject=g;` | Linear mixed model with REML | `RANDOM` vs `REPEATED` confusion (Rule 4) |
| `CLASS` (MIXED) | `class pat_id region treatment;` | Declare categorical predictors + subject var | Omitting subject var → silent wrong blocking |
| `MODEL ... / ddfm=kr` | `model y = x / ddfm=kr solution;` | Kenward-Roger DDF (standard for unbalanced) | Default Satterthwaite — fine but be explicit |
| `RANDOM` (MIXED) | `random intercept / subject=id;` | G-side random effects | Using it for residual serial correlation |
| `REPEATED` (MIXED) | `repeated visit / subject=id type=ar(1);` | R-side within-subject correlation | Using it for a random intercept |
| `TYPE=` | `type=ar(1)` / `type=cs` / `type=un` | Covariance structure | `type=un` on wide data — non-convergence |
| `LSMEANS` | `lsmeans trt / diff cl;` | Covariate-adjusted marginal means | Treating as raw group means (Rule 8) |

## Silent Pitfalls

- **Numeric categorical as continuous** — see Rule 1. Includes
  `SUBJECT=` variables: the subject ID must be in `CLASS` or blocking
  is silently broken.
- **MIXED `RANDOM` vs `REPEATED` confusion** — the two modify
  different covariance matrices (`G` vs `R`). Using one where the
  other was meant fits a different model entirely. See Rule 4.
- **Reporting `MEANS` output as "adjusted"** — `PROC MEANS` produces
  arithmetic means, not covariate-adjusted (LS) means. See Rule 8.
- **`type=un` non-convergence on wide panels** — unstructured
  covariance has O(n^2) parameters; estimation fails or produces
  non-positive-definite `G` on long time series. Start with
  `type=ar(1)` or `type=cs`.

## Anti-patterns

- `proc mixed; ... random visit / type=ar(1);` when within-subject
  residual AR(1) was meant → see Rule 4. Use `REPEATED`.
- Using `PROC GLM` on clustered / repeated-measures data and
  reporting the SEs → move to MIXED.
- `LSMEANS` reported alongside `PROC MEANS` output with no
  distinction → readers assume they're the same thing. They're not.
