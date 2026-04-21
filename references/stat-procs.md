---
title: Statistical procedures reference
scope: PROC LOGISTIC, GLM, MIXED, GENMOD, SURVEY* (SURVEYFREQ / SURVEYMEANS / SURVEYLOGISTIC / SURVEYREG), LIFETEST, PHREG — model syntax, options, and ODS OUTPUT names.
loaded_when: PROC LOGISTIC / GLM / MIXED / GENMOD / SURVEY* / LIFETEST / PHREG, or any modeling or survey-weighted analysis task.
last_reviewed: 2026-04-21
reviewer: xiaosongz
---

## Overview

The statistical procedures covered here — LOGISTIC, GLM, MIXED,
GENMOD, LIFETEST, PHREG, and the SURVEY* family — share a design
ethos inherited from the original SAS/STAT User's Guide: every proc
takes a `CLASS` statement for categorical predictors, a `MODEL`
statement for fixed effects, and uses silent defaults for response
ordering, link function, and variance structure that are almost
always wrong for claims-data work. The default response-level
ordering in LOGISTIC models `P(Y = lowest ordinal value)` — i.e. the
wrong event for most binary outcomes. GENMOD defaults to
`DIST=NORMAL LINK=IDENTITY`, which is OLS masquerading as GLM.
SURVEYMEANS with no `STRATA` / `CLUSTER` / `WEIGHT` assumes simple
random sampling; real complex-survey data yields silently wrong SEs.

This file encodes the rules from the SAS/STAT User's Guide chapters
on LOGISTIC (ch. 76), GLM (ch. 50), MIXED (ch. 81), GENMOD (ch. 48),
LIFETEST (ch. 74), PHREG (ch. 89), and SURVEYMEANS (ch. 118). The
focus is on silent-default pitfalls — the places where the procedure
runs to completion, produces a plausible-looking output, and is
flatly wrong because the programmer did not override a default. These
procedures do not return data to macros; capture structured model
objects via `ODS OUTPUT` (Rule 7) instead.

For base-level categorical summaries (FREQ, MEANS, UNIVARIATE) see
`base-procs.md`; for PROC SQL see `proc-sql.md`; for the DATA-step
preprocessing that typically precedes these procs see `data-step.md`.

## Critical Rules

### Rule 1: `CLASS` is required for every categorical predictor — a numeric categorical in `MODEL` without `CLASS` is silently treated as continuous

Source: https://documentation.sas.com/doc/en/statug/9.4/statug.htm

LOGISTIC, GLM, MIXED, and GENMOD all accept a `CLASS` statement that
names the categorical predictors. Any predictor listed in `MODEL`
but not in `CLASS` is treated as continuous — a classic claims-data
bug where `sex` coded as 1/2 or `region` coded 1–4 yields a
"one-unit increase in sex" coefficient rather than the intended
F-vs-M contrast. The procedure runs silently; the fix is trivial,
the symptom is not.

```sas
/* CORRECT - sex and region in CLASS, parameterized as reference coding */
proc logistic data=claims descending;
  class sex(ref='F') region(ref='1') / param=ref;
  model had_event(event='1') = age sex region;
run;
```

```sas
/* WRONG - sex is 1/2 numeric; treated as continuous. Coefficient is the
   "one-unit change in sex" log-odds, not the F-vs-M contrast. */
proc logistic data=claims descending;
  model had_event(event='1') = age sex region;
run;
```

### Rule 2: LOGISTIC defaults to modeling `P(Y = lowest ordinal value)` — use `descending` or `event='value'` to pin the event

Source: https://documentation.sas.com/doc/en/statug/9.4/statug.htm

Per the LOGISTIC Procedure documentation, the default model is the
probability of the lowest response level — so for a binary outcome
coded 0 / 1, LOGISTIC models `P(Y = 0)` unless told otherwise. Two
idiomatic fixes: `proc logistic descending;` flips the ordering so
the higher value is the event, or `model y(event='1') = ...` names
the event explicitly in the MODEL statement (preferred — self-
documenting and survives reordering).

```sas
/* CORRECT - event='1' makes the intent unambiguous */
proc logistic data=claims;
  class sex(ref='F') / param=ref;
  model had_event(event='1') = age sex / clparm=pl;
run;
```

```sas
/* WRONG - models P(had_event = 0); odds ratios point the wrong way */
proc logistic data=claims;
  class sex(ref='F') / param=ref;
  model had_event = age sex;
run;
```

### Rule 3: GENMOD defaults to `DIST=NORMAL LINK=IDENTITY` — specify both for logistic, Poisson, or gamma

Source: https://documentation.sas.com/doc/en/statug/9.4/statug.htm

Per the GENMOD MODEL statement docs, "if you specify no distribution
and no link function, then the GENMOD procedure defaults to the
normal distribution with the identity link function" — i.e. OLS.
This is almost never what a GLM user wants. For binary outcomes
specify `dist=bin link=logit`; for counts `dist=poisson link=log`;
for skewed costs `dist=gamma link=log`. When you specify `DIST=` but
not `LINK=`, the canonical link for that distribution is used.

```sas
/* CORRECT - binary outcome as logistic regression via GENMOD */
proc genmod data=claims;
  class sex(ref='F') region / param=ref;
  model had_event(event='1') = age sex region
        / dist=bin link=logit;
run;
```

```sas
/* WRONG - no DIST/LINK; GENMOD fits OLS to a 0/1 response.
   Coefficients look plausible but standard errors are nonsense. */
proc genmod data=claims;
  class sex region;
  model had_event = age sex region;
run;
```

### Rule 4: MIXED `REPEATED` models R-side (within-subject residual correlation); `RANDOM` models G-side (random effects) — they are NOT interchangeable

Source: https://documentation.sas.com/doc/en/statug/9.4/statug.htm

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

### Rule 5: LIFETEST `TIME t*status(code)` — the value in parentheses is the CENSORED code, not the event code

Source: https://documentation.sas.com/doc/en/statug/9.4/statug.htm

Per the LIFETEST Getting Started section, the syntax is
`time <time-var>*<status-var>(<censor-value-list>);` — the values in
parens are the CENSORED codes. The most common bug is writing
`time days*event(1)` expecting to "mark event as 1," producing a
flat survival curve because every event observation was censored
instead. Use `event(0)` when 0 = censored, 1 = event (the typical
convention); `event(1)` when 1 = censored.

```sas
/* CORRECT - status=0 means censored, 1 means event. (0) is CENSOR code. */
proc lifetest data=surv plots=survival(atrisk);
  time days*status(0);
  strata treatment;
run;
```

```sas
/* WRONG - (1) marks event observations as censored; survival curve
   looks 100% because no events are counted. */
proc lifetest data=surv;
  time days*status(1);  /* flipped - this marks events as censored */
  strata treatment;
run;
```

### Rule 6: SURVEY* procs require design variables — no `STRATA` / `CLUSTER` / `WEIGHT` assumes simple random sampling (wrong SEs)

Source: https://documentation.sas.com/doc/en/statug/9.4/statug.htm

Per the SURVEYMEANS Procedure overview, the SURVEY family (MEANS,
FREQ, LOGISTIC, REG, PHREG) estimates sampling errors under a
complex sample design — stratification, clustering, unequal
weighting. Omit the design statements and the procedure silently
assumes SRS, producing point estimates that are fine but variances,
CIs, and p-values that are all wrong. For NHANES, BRFSS, MEPS,
claims samples with weights, the `STRATA` / `CLUSTER` / `WEIGHT`
triad is not optional.

```sas
/* CORRECT - full complex-survey design declared */
proc surveymeans data=nhanes;
  strata sdmvstra;
  cluster sdmvpsu;
  weight wtmec2yr;
  var bmxbmi sbp;
run;
```

```sas
/* WRONG - no design variables; SEs computed as if SRS from a finite
   population. Point estimates OK; inference invalid. */
proc surveymeans data=nhanes;
  var bmxbmi sbp;
run;
```

### Rule 7: None of these procs return data to macros — use `ODS OUTPUT` to capture structured model output

Source: https://documentation.sas.com/doc/en/statug/9.4/statug.htm

LOGISTIC, GLM, MIXED, GENMOD, LIFETEST, PHREG, and the SURVEY* procs
write their tabular output through the Output Delivery System, not
through macro variables or a SAS dataset by default. To feed
parameter estimates / odds ratios / LS-means to a downstream step,
wrap the proc in `ODS OUTPUT <TableName>=<outds>;`. Table names are
documented per-proc (`ParameterEstimates`, `OddsRatios`, `LSMeans`,
`ModelFit`, `ConvergenceStatus`, etc.) and are case-sensitive in the
ODS OUTPUT clause. Without `ODS OUTPUT`, the only way to "get the
coefficient" into downstream code is to parse the printed listing —
brittle and unnecessary.

```sas
/* CORRECT - capture parameter estimates to a dataset via ODS OUTPUT */
ods output ParameterEstimates=lr_pe OddsRatios=lr_or;
proc logistic data=claims;
  class sex(ref='F') region / param=ref;
  model had_event(event='1') = age sex region;
run;
ods output close;

proc print data=lr_pe; run;  /* coefficients now accessible */
```

```sas
/* WRONG - no ODS OUTPUT; coefficients only in the printed listing */
proc logistic data=claims;
  class sex / param=ref;
  model had_event(event='1') = age sex;
run;
/* downstream code has no dataset to read the OR from */
```

### Rule 8: `LSMEANS` in GLM / MIXED / GENMOD produces covariate-adjusted (marginal) means — NOT arithmetic means

Source: https://documentation.sas.com/doc/en/statug/9.4/statug.htm

`lsmeans class-effect;` computes the least-squares means — the
predicted value at a common set of covariate values, effectively the
"adjusted" mean holding other model covariates at their mean / first
level. It is NOT the simple arithmetic mean per group; that is what
`proc means; class g; var x;` gives you. Reporting LSMEANS as "group
means" or the `MEAN` statement output as "adjusted means" is a
common write-up error. Use the right one for the question: raw
descriptive → `PROC MEANS`; marginal (adjusted for model
covariates) → `LSMEANS`.

```sas
/* CORRECT - LSMEANS gives the covariate-adjusted mean per treatment */
proc mixed data=trial;
  class treatment center;
  model outcome = treatment center age baseline;
  lsmeans treatment / diff cl;
run;
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

### Idiom: Logistic regression for a binary claims outcome with CLASS + ODS OUTPUT capture

Source: https://documentation.sas.com/doc/en/statug/9.4/statug.htm

Purpose: fit a logistic regression for a binary outcome (hospital
readmission, event occurrence), with categorical predictors properly
declared via `CLASS`, the event pinned to the intended level, and
parameter estimates plus odds ratios captured to SAS datasets for
downstream reporting.

```sas
ods output ParameterEstimates=lr_pe
           OddsRatios=lr_or
           ModelInfo=lr_mi;
proc logistic data=claims;
  class sex(ref='F') region(ref='1') / param=ref;
  model readmit_30d(event='1') = age sex region prior_admits
        / clparm=pl;
  oddsratio age;
  oddsratio sex;
run;
ods output close;
```

### Idiom: Mixed model for panel claims with random patient intercept

Source: https://documentation.sas.com/doc/en/statug/9.4/statug.htm

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

### Idiom: Kaplan-Meier survival curve by treatment with log-rank test

Source: https://documentation.sas.com/doc/en/statug/9.4/statug.htm

Purpose: compare survival (time to death, time to readmission)
across treatment groups. `time days*event(0)` declares 0 as the
censoring code; `strata treatment` produces one curve per group and
the log-rank test of equality; `plots=survival(atrisk)` adds the
at-risk table below the curve.

```sas
ods output HomTests=lr_test ProductLimitEstimates=ple;
proc lifetest data=surv plots=survival(atrisk cb=hw);
  time days*event(0);
  strata treatment;
run;
ods output close;
```

### Idiom: Cox proportional hazards via PHREG with hazard ratios

Source: https://documentation.sas.com/doc/en/statug/9.4/statug.htm

Purpose: semi-parametric survival model with covariate adjustment.
PHREG's MODEL syntax mirrors LIFETEST (`time*status(censor_code)`),
with `CLASS` for categorical predictors and `HAZARDRATIO` for
per-covariate HR estimates with confidence limits.

```sas
ods output ParameterEstimates=cox_pe HazardRatios=cox_hr;
proc phreg data=surv;
  class sex(ref='F') treatment(ref='placebo') / param=ref;
  model days*event(0) = age sex treatment;
  hazardratio treatment;
  hazardratio age;
run;
ods output close;
```

### Idiom: Complex-survey proportion via SURVEYFREQ with STRATA / CLUSTER / WEIGHT

Source: https://documentation.sas.com/doc/en/statug/9.4/statug.htm

Purpose: estimate a population proportion from a complex-sample
survey (NHANES-style design) with correct variance estimation. Every
design variable from the codebook is declared; the `tables / row cl`
syntax produces row percentages with confidence limits that
correctly account for the stratified clustered design.

```sas
proc surveyfreq data=nhanes;
  strata sdmvstra;
  cluster sdmvpsu;
  weight wtmec2yr;
  tables age_cat * had_event / row cl;
run;
```

## Function / Statement Quick Ref

| Name | Syntax | Purpose | Common mistake | Doc URL |
|------|--------|---------|----------------|---------|
| `PROC LOGISTIC` | `proc logistic data=ds; class ...; model y(event='1') = x;` | Binary / ordinal / nominal logistic regression | Default models P(lowest value); omit `event=` | [`PROC LOGISTIC`](https://documentation.sas.com/doc/en/statug/9.4/statug.htm) |
| `CLASS` (LOGISTIC) | `class sex(ref='F') / param=ref;` | Declare categorical predictors + reference coding | Numeric categorical missing from CLASS → continuous | [`CLASS Statement`](https://documentation.sas.com/doc/en/statug/9.4/statug.htm) |
| `MODEL event=` | `model y(event='1') = x;` | Pin modeled event in LOGISTIC | Omitting → wrong event modeled | [`MODEL Statement`](https://documentation.sas.com/doc/en/statug/9.4/statug.htm) |
| `descending` | `proc logistic descending;` | Flip response ordering (alternate to `event=`) | Using both — redundant, confusing | [`PROC LOGISTIC`](https://documentation.sas.com/doc/en/statug/9.4/statug.htm) |
| `PROC GLM` | `proc glm; class g; model y = g x;` | ANOVA / ANCOVA / linear regression | Treating a fit as MIXED when data are clustered | [`PROC GLM`](https://documentation.sas.com/doc/en/statug/9.4/statug.htm) |
| `PROC MIXED` | `proc mixed; class g; model y = x; random intercept / subject=g;` | Linear mixed model with REML | `RANDOM` vs `REPEATED` confusion (Rule 4) | [`PROC MIXED`](https://documentation.sas.com/doc/en/statug/9.4/statug.htm) |
| `RANDOM` (MIXED) | `random intercept / subject=id;` | G-side random effects | Using it for residual serial correlation | [`RANDOM Statement`](https://documentation.sas.com/doc/en/statug/9.4/statug.htm) |
| `REPEATED` (MIXED) | `repeated visit / subject=id type=ar(1);` | R-side within-subject correlation | Using it for a random intercept | [`REPEATED Statement`](https://documentation.sas.com/doc/en/statug/9.4/statug.htm) |
| `PROC GENMOD` | `proc genmod; class g; model y = x / dist=bin link=logit;` | Generalized linear model | Default `DIST=NORMAL LINK=IDENTITY` (OLS) | [`PROC GENMOD`](https://documentation.sas.com/doc/en/statug/9.4/statug.htm) |
| `DIST=` (GENMOD) | `model y = x / dist=poisson;` | Response distribution family | Forgetting it → silent OLS fit (Rule 3) | [`MODEL Statement`](https://documentation.sas.com/doc/en/statug/9.4/statug.htm) |
| `LINK=` (GENMOD) | `model y = x / dist=bin link=logit;` | Link function | Omitting with DIST= → canonical link used | [`MODEL Statement`](https://documentation.sas.com/doc/en/statug/9.4/statug.htm) |
| `PROC LIFETEST` | `proc lifetest; time t*c(0); strata g;` | Nonparametric survival (K-M) | `time t*c(1)` flipping the censor code (Rule 5) | [`PROC LIFETEST`](https://documentation.sas.com/doc/en/statug/9.4/statug.htm) |
| `TIME time*status(c)` | `time days*event(0);` | Declare survival time + CENSOR code | Value in parens is CENSORED, not event | [`TIME Statement`](https://documentation.sas.com/doc/en/statug/9.4/statug.htm) |
| `PROC PHREG` | `proc phreg; class g; model t*c(0) = x;` | Cox proportional hazards regression | Same TIME syntax pitfall as LIFETEST | [`PROC PHREG`](https://documentation.sas.com/doc/en/statug/9.4/statug.htm) |
| `HAZARDRATIO` | `hazardratio treatment;` | Per-covariate HR with CIs | Reporting parameter estimates as HRs (wrong scale) | [`HAZARDRATIO`](https://documentation.sas.com/doc/en/statug/9.4/statug.htm) |
| `PROC SURVEYMEANS` | `proc surveymeans; strata s; cluster c; weight w; var y;` | Complex-survey descriptives | Omitting design vars → SRS variance (Rule 6) | [`PROC SURVEYMEANS`](https://documentation.sas.com/doc/en/statug/9.4/statug.htm) |
| `PROC SURVEYFREQ` | `proc surveyfreq; strata s; cluster c; weight w; tables a*b;` | Complex-survey crosstabs | Same design-var omission pitfall | [`PROC SURVEYFREQ`](https://documentation.sas.com/doc/en/statug/9.4/statug.htm) |
| `PROC SURVEYLOGISTIC` | `proc surveylogistic; strata s; cluster c; weight w; model y=x;` | Complex-survey logistic | Using PROC LOGISTIC with `weight` → wrong SEs | [`PROC SURVEYLOGISTIC`](https://documentation.sas.com/doc/en/statug/9.4/statug.htm) |
| `LSMEANS` | `lsmeans trt / diff cl;` | Covariate-adjusted marginal means | Treating as raw group means (Rule 8) | [`LSMEANS Statement`](https://documentation.sas.com/doc/en/statug/9.4/statug.htm) |
| `ODS OUTPUT` | `ods output ParameterEstimates=pe;` | Capture tabular output to a dataset | Wrong table name → empty / missing dataset | [`ODS OUTPUT`](https://documentation.sas.com/doc/en/statug/9.4/statug.htm) |

## Silent Pitfalls

- **Numeric categorical as continuous** — any categorical predictor
  coded numerically (sex=1/2, region=1..4) that is omitted from
  `CLASS` is silently modeled as continuous. The "coefficient for
  sex" becomes a per-unit log-odds; the F-vs-M contrast vanishes.
  See Rule 1.
  Source: https://documentation.sas.com/doc/en/statug/9.4/statug.htm

- **Wrong event in LOGISTIC** — the default models the probability
  of the LOWEST response level, not the highest. For binary
  outcomes coded 0/1, you almost certainly mean `event='1'`. See
  Rule 2.
  Source: https://documentation.sas.com/doc/en/statug/9.4/statug.htm

- **GENMOD defaulting to OLS** — `proc genmod; model y = x; run;`
  with a 0/1 response silently fits a normal-identity model. All
  coefficients are linear-probability estimates; CIs and p-values
  are meaningless for binary data. See Rule 3.
  Source: https://documentation.sas.com/doc/en/statug/9.4/statug.htm

- **MIXED `RANDOM` vs `REPEATED` confusion** — the two modify
  different covariance matrices (`G` vs `R`). Using one where the
  other was meant fits a different model entirely. See Rule 4.
  Source: https://documentation.sas.com/doc/en/statug/9.4/statug.htm

- **Inverted LIFETEST/PHREG censor code** — `time days*event(1)`
  when 1 is the event (not censoring) marks every event observation
  as censored. Survival curves look artificially high; log-rank
  tests are nonsense. See Rule 5.
  Source: https://documentation.sas.com/doc/en/statug/9.4/statug.htm

- **SURVEY* without design vars** — omitting `STRATA` / `CLUSTER` /
  `WEIGHT` silently assumes SRS. Point estimates are usually close
  to correct; SEs, CIs, and p-values are all wrong. See Rule 6.
  Source: https://documentation.sas.com/doc/en/statug/9.4/statug.htm

- **Reporting `MEANS` output as "adjusted"** — `PROC MEANS` produces
  arithmetic means, not covariate-adjusted (LS) means. Labeling them
  "adjusted" in a report is a write-up error. See Rule 8.
  Source: https://documentation.sas.com/doc/en/statug/9.4/statug.htm

## Anti-patterns (STOP signs)

**STOP** when you see any of the following — the procedure runs to
completion but the output is almost certainly not what the author
meant:

- `proc logistic; model y = x; run;` where `x` is a numeric coded
  categorical (sex=1/2, region=1..4) and no `CLASS` statement →
  see Rule 1. Silent continuous fit.
- `proc logistic; model y = x;` with no `event=` and no
  `descending` → see Rule 2. Models P(y=0).
- `proc genmod; model y = x; run;` with no `dist=` / `link=` on a
  non-normal outcome → see Rule 3. Silent OLS.
- `proc mixed; ... random visit / type=ar(1);` when within-subject
  residual AR(1) was meant → see Rule 4. Use `REPEATED`.
- `time days*event(1);` with `event` coded 0=censor 1=event → see
  Rule 5. Inverted censor code; every event censored.
- `proc surveymeans; var y; run;` on a complex-sample dataset with
  no `STRATA` / `CLUSTER` / `WEIGHT` → see Rule 6. Wrong SEs.
- Reporting `lr_pe` parameter estimates directly as odds ratios →
  log-odds scale, not OR. Request `OddsRatios` via ODS OUTPUT.
- Reporting `PROC MEANS` output as "covariate-adjusted" → see
  Rule 8. LSMEANS gives adjusted; MEANS does not.

## See Also

- [base-procs.md](base-procs.md) — PROC FREQ for descriptive
  categorical summaries; PROC MEANS / UNIVARIATE for arithmetic
  means and quantiles (contrast with Rule 8 LSMEANS).
- [data-step.md](data-step.md) — preprocessing patterns (variable
  recoding, survival-time construction) that typically precede
  these procs.
- [proc-sql.md](proc-sql.md) — building the analysis dataset via
  SQL joins before model fitting.
- [ods-and-output.md](ods-and-output.md) — routing ODS OUTPUT to
  Excel / RTF / PDF; controlling which tables are captured.
- [SAS/STAT User's Guide](https://documentation.sas.com/doc/en/statug/9.4/statug.htm)
