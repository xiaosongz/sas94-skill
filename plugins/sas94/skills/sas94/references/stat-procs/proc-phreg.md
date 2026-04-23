---
title: PROC PHREG rules
loaded_when: PROC PHREG, Cox proportional hazards regression, time-to-event with covariate adjustment, HAZARDRATIO statement, semi-parametric survival model.
---

## Critical Rules

### Rule 1: `CLASS` is required for every categorical predictor — a numeric categorical in `MODEL` without `CLASS` is silently treated as continuous

PHREG accepts a `CLASS` statement (SAS 9.2+) that names the
categorical predictors. Any predictor listed in `MODEL` but not in
`CLASS` is treated as continuous — `treatment` coded 1/2/3 becomes
a per-unit log-hazard trend instead of the intended group contrasts.

```sas
/* CORRECT - sex and treatment declared; reference coding */
proc phreg data=surv;
  class sex(ref='F') treatment(ref='placebo') / param=ref;
  model days*event(0) = age sex treatment;
  hazardratio treatment;
run;
```

```sas
/* WRONG - treatment 1/2/3 numeric; treated as continuous dose */
proc phreg data=surv;
  model days*event(0) = age treatment;
run;
```

### Rule 5: PHREG `MODEL t*status(code)` — the value in parentheses is the CENSORED code, not the event code

Same `TIME` censor-code syntax as LIFETEST, embedded in the `MODEL`
statement: `model <time>*<status>(<censor-value-list>) = <covs>;`
The parenthesized values are CENSORED codes. Writing
`model days*event(1) = age` when 1 is the event marks every event
observation as censored; the Cox partial likelihood is fit on zero
events and all coefficients become meaningless (or estimation
fails silently).

```sas
/* CORRECT - status=0 means censored, 1 means event. (0) is CENSOR code. */
proc phreg data=surv;
  class treatment(ref='placebo') / param=ref;
  model days*event(0) = age treatment;
  hazardratio treatment;
run;
```

```sas
/* WRONG - (1) marks event observations as censored; no events fitted. */
proc phreg data=surv;
  model days*event(1) = age treatment;
run;
```

## Canonical Idioms

### Idiom: Cox proportional hazards via PHREG with hazard ratios

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

## Quick Ref

| Name | Syntax | Purpose | Common mistake |
|------|--------|---------|----------------|
| `PROC PHREG` | `proc phreg; class g; model t*c(0) = x;` | Cox proportional hazards regression | Same TIME syntax pitfall as LIFETEST |
| `MODEL time*status(c)` | `model days*event(0) = age trt;` | Cox partial likelihood + CENSOR code | Value in parens is CENSORED, not event |
| `CLASS` (PHREG) | `class treatment(ref='placebo') / param=ref;` | Declare categorical predictors + reference | Numeric categorical missing from CLASS → continuous |
| `HAZARDRATIO` | `hazardratio treatment;` | Per-covariate HR with CIs | Reporting parameter estimates as HRs (wrong scale) |
| `ODS OUTPUT` | `ods output ParameterEstimates=pe HazardRatios=hr;` | Capture coefficients / HRs | Wrong table name → empty dataset |

## Silent Pitfalls

- **Inverted PHREG censor code** — `days*event(1)` when 1 is the
  event marks every event as censored; partial likelihood fits on
  zero events. See Rule 5.
- **Numeric categorical as continuous** — see Rule 1.
- **Parameter estimates reported as hazard ratios** — `cox_pe` is
  on the log-hazard scale; request `HazardRatios` via ODS OUTPUT
  for HR output with CIs.
- **PH assumption unverified** — PHREG does not test the
  proportional-hazards assumption by default. Use `assess
  ph / resample;` or a time-interaction term to check.

## Anti-patterns

- `model days*event(1) = age;` with 1 = event → see Rule 5.
  Inverted censor code; every event censored.
- Reporting the `ParameterEstimates` table directly as hazard
  ratios → log-hazard scale, not HR. Request `HazardRatios` via
  ODS OUTPUT.
- Fitting PHREG on complex-survey data without design variables →
  use `PROC SURVEYPHREG` (see `proc-surveymeans.md`).
