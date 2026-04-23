---
title: SURVEY* family rules (SURVEYMEANS / SURVEYFREQ / SURVEYLOGISTIC / SURVEYREG)
loaded_when: Complex-sample survey analysis (NHANES, BRFSS, MEPS, claims weighted samples), PROC SURVEYMEANS / SURVEYFREQ / SURVEYLOGISTIC / SURVEYREG / SURVEYPHREG, or any mention of STRATA + CLUSTER + WEIGHT design.
---

## Critical Rules

### Rule 6: SURVEY* procs require design variables — no `STRATA` / `CLUSTER` / `WEIGHT` assumes simple random sampling (wrong SEs)

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

## Canonical Idioms

### Idiom: Complex-survey proportion via SURVEYFREQ with STRATA / CLUSTER / WEIGHT

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

### Idiom: Survey-weighted logistic regression

Purpose: design-based logistic regression — like PROC LOGISTIC but
with correct SEs for complex-survey data. Same `CLASS` /
`MODEL event=` rules as LOGISTIC (see `proc-logistic.md`), plus the
`STRATA` / `CLUSTER` / `WEIGHT` design triad.

```sas
ods output ParameterEstimates=sl_pe OddsRatios=sl_or;
proc surveylogistic data=nhanes;
  strata sdmvstra;
  cluster sdmvpsu;
  weight wtmec2yr;
  class sex(ref='F') / param=ref;
  model had_event(event='1') = age sex;
run;
ods output close;
```

## Quick Ref

| Name | Syntax | Purpose | Common mistake |
|------|--------|---------|----------------|
| `PROC SURVEYMEANS` | `proc surveymeans; strata s; cluster c; weight w; var y;` | Complex-survey descriptives | Omitting design vars → SRS variance (Rule 6) |
| `PROC SURVEYFREQ` | `proc surveyfreq; strata s; cluster c; weight w; tables a*b;` | Complex-survey crosstabs | Same design-var omission pitfall |
| `PROC SURVEYLOGISTIC` | `proc surveylogistic; strata s; cluster c; weight w; model y=x;` | Complex-survey logistic | Using PROC LOGISTIC with `weight` → wrong SEs |
| `PROC SURVEYREG` | `proc surveyreg; strata s; cluster c; weight w; model y = x;` | Complex-survey linear regression | Using PROC GLM with `weight` → wrong SEs |
| `STRATA` | `strata sdmvstra;` | Design strata (independent selection units) | Omitting → SRS inference |
| `CLUSTER` | `cluster sdmvpsu;` | Primary sampling units (PSUs) | Omitting → SRS inference |
| `WEIGHT` | `weight wtmec2yr;` | Sampling weight (inverse selection prob) | Using unweighted data → biased point estimates |

## Silent Pitfalls

- **SURVEY* without design vars** — omitting `STRATA` / `CLUSTER` /
  `WEIGHT` silently assumes SRS. Point estimates are usually close
  to correct; SEs, CIs, and p-values are all wrong. See Rule 6.
- **Using PROC LOGISTIC `weight` on complex-survey data** — the
  `WEIGHT` statement in non-SURVEY procs treats weights as frequency
  / precision weights, NOT sampling weights. SEs are wrong. Move to
  `PROC SURVEYLOGISTIC`.
- **Using PROC MEANS / FREQ `weight` on complex-survey data** —
  same trap. Use `PROC SURVEYMEANS` / `PROC SURVEYFREQ`.
- **Subset via `WHERE` on survey data** — drops PSUs / strata from
  the variance calculation. Use `DOMAIN` statement instead for
  subpopulation analysis so the variance estimation sees the full
  design.

## Anti-patterns

- `proc surveymeans; var y; run;` on a complex-sample dataset with
  no `STRATA` / `CLUSTER` / `WEIGHT` → see Rule 6. Wrong SEs.
- `proc logistic; weight wt; model y=x;` on NHANES-style data →
  wrong variance model. Use `PROC SURVEYLOGISTIC`.
- Using a `WHERE` to subset survey data for subgroup estimates →
  variance calculation is wrong. Use `DOMAIN` instead.
- Ignoring the FPC (finite population correction) `TOTAL=` /
  `RATE=` option when the sampling fraction is non-negligible.
