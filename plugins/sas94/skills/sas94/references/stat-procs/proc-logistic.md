---
title: PROC LOGISTIC rules
loaded_when: PROC LOGISTIC, binary/ordinal/nominal logistic regression, odds ratios, CLASS + reference coding, or any `event=` / `descending` question.
---

## Critical Rules

### Rule 1: `CLASS` is required for every categorical predictor — a numeric categorical in `MODEL` without `CLASS` is silently treated as continuous

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

## Canonical Idioms

### Idiom: Logistic regression for a binary claims outcome with CLASS + ODS OUTPUT capture

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

## Quick Ref

| Name | Syntax | Purpose | Common mistake |
|------|--------|---------|----------------|
| `PROC LOGISTIC` | `proc logistic data=ds; class ...; model y(event='1') = x;` | Binary / ordinal / nominal logistic regression | Default models P(lowest value); omit `event=` |
| `CLASS` (LOGISTIC) | `class sex(ref='F') / param=ref;` | Declare categorical predictors + reference coding | Numeric categorical missing from CLASS → continuous |
| `MODEL event=` | `model y(event='1') = x;` | Pin modeled event in LOGISTIC | Omitting → wrong event modeled |
| `descending` | `proc logistic descending;` | Flip response ordering (alternate to `event=`) | Using both — redundant, confusing |
| `ODS OUTPUT` | `ods output ParameterEstimates=pe OddsRatios=or;` | Capture coefficients + ORs to datasets | Wrong table name → empty / missing dataset |

## Silent Pitfalls

- **Numeric categorical as continuous** — any categorical predictor
  coded numerically (sex=1/2, region=1..4) that is omitted from
  `CLASS` is silently modeled as continuous. The "coefficient for
  sex" becomes a per-unit log-odds; the F-vs-M contrast vanishes.
  See Rule 1.
- **Wrong event in LOGISTIC** — the default models the probability
  of the LOWEST response level, not the highest. For binary
  outcomes coded 0/1, you almost certainly mean `event='1'`. See
  Rule 2.
- **Parameter estimates reported as odds ratios** — `lr_pe` is on
  the log-odds scale; request `OddsRatios` via `ODS OUTPUT` for OR
  output with CIs.

## Anti-patterns

- `proc logistic; model y = x; run;` where `x` is a numeric coded
  categorical (sex=1/2, region=1..4) and no `CLASS` statement →
  see Rule 1. Silent continuous fit.
- `proc logistic; model y = x;` with no `event=` and no
  `descending` → see Rule 2. Models P(y=0).
- Reporting `ParameterEstimates` values directly as odds ratios —
  log-odds scale, not OR. Request `OddsRatios` via ODS OUTPUT.
- Using PROC LOGISTIC with a `weight` statement on complex-survey
  data → wrong SEs. Use `PROC SURVEYLOGISTIC` (see
  `proc-surveymeans.md`).
