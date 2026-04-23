---
title: PROC GENMOD rules
loaded_when: PROC GENMOD, generalized linear models, Poisson / binomial / gamma / negative-binomial fits, GEE (`REPEATED SUBJECT=`), log / logit / identity link selection.
---

## Critical Rules

### Rule 1: `CLASS` is required for every categorical predictor — a numeric categorical in `MODEL` without `CLASS` is silently treated as continuous

GENMOD (together with LOGISTIC, GLM, MIXED) accepts a `CLASS`
statement that names the categorical predictors. Any predictor
listed in `MODEL` but not in `CLASS` is treated as continuous.

```sas
/* CORRECT - sex and region declared; reference coding */
proc genmod data=claims;
  class sex(ref='F') region / param=ref;
  model had_event(event='1') = age sex region
        / dist=bin link=logit;
run;
```

```sas
/* WRONG - sex 1/2 numeric; treated as continuous */
proc genmod data=claims;
  model had_event(event='1') = age sex region
        / dist=bin link=logit;
run;
```

### Rule 3: GENMOD defaults to `DIST=NORMAL LINK=IDENTITY` — specify both for logistic, Poisson, or gamma

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

## Canonical Idioms

### Idiom: Poisson regression for event counts with offset

Purpose: model count outcomes (ED visits, admissions) with a log
link and an exposure offset so coefficients are interpretable as
log-rate-ratios. `dist=poisson link=log`; `offset=log_person_years`
divides count by exposure on the linear-predictor scale.

```sas
ods output ParameterEstimates=gm_pe ModelFit=gm_fit;
proc genmod data=counts;
  class sex(ref='F') region / param=ref;
  model ed_visits = age sex region
        / dist=poisson link=log offset=log_person_years;
run;
ods output close;
```

### Idiom: GEE with REPEATED SUBJECT= for clustered binary data

Purpose: population-averaged estimates for clustered/longitudinal
binary data. `REPEATED SUBJECT=` declares the clustering with a
working correlation structure (exchangeable / AR(1) / unstructured);
SEs are robust (empirical sandwich).

```sas
proc genmod data=longitudinal descending;
  class pat_id visit treatment(ref='control') / param=ref;
  model had_event = treatment visit / dist=bin link=logit;
  repeated subject=pat_id / type=exch;
run;
```

## Quick Ref

| Name | Syntax | Purpose | Common mistake |
|------|--------|---------|----------------|
| `PROC GENMOD` | `proc genmod; class g; model y = x / dist=bin link=logit;` | Generalized linear model | Default `DIST=NORMAL LINK=IDENTITY` (OLS) |
| `DIST=` (GENMOD) | `model y = x / dist=poisson;` | Response distribution family | Forgetting it → silent OLS fit (Rule 3) |
| `LINK=` (GENMOD) | `model y = x / dist=bin link=logit;` | Link function | Omitting with DIST= → canonical link used |
| `OFFSET=` | `model y = x / dist=poisson link=log offset=loge;` | Exposure offset on link scale | Passing raw exposure — need log-transform first |
| `REPEATED SUBJECT=` | `repeated subject=id / type=exch;` | GEE working correlation | Treating as random effect — it's marginal, not conditional |
| `ODS OUTPUT` | `ods output ParameterEstimates=pe GEEEmpPEst=gee;` | Capture coefficients / GEE estimates | Wrong table name — GEE uses `GEEEmpPEst`, not `ParameterEstimates` |

## Silent Pitfalls

- **GENMOD defaulting to OLS** — `proc genmod; model y = x; run;`
  with a 0/1 response silently fits a normal-identity model. All
  coefficients are linear-probability estimates; CIs and p-values
  are meaningless for binary data. See Rule 3.
- **Numeric categorical as continuous** — same trap as LOGISTIC/GLM;
  see Rule 1.
- **Poisson without offset** — modeling counts but omitting
  `offset=log_exposure` compares raw counts across exposure units of
  different size; results are silently wrong.
- **GEE vs random-effects confusion** — `REPEATED SUBJECT=` in
  GENMOD is population-averaged (marginal); `RANDOM ... SUBJECT=` in
  MIXED / GLIMMIX is subject-specific (conditional). Different
  estimands.

## Anti-patterns

- `proc genmod; model y = x; run;` with no `dist=` / `link=` on a
  non-normal outcome → see Rule 3. Silent OLS.
- Poisson regression on counts with no `offset=` and no denominator
  variable → rate comparisons are apples-to-oranges.
- Reading `ParameterEstimates` ODS table after a GEE fit — the GEE
  estimates are in `GEEEmpPEst`.
