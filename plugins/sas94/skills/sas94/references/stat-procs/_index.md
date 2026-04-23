---
title: Statistical procedures - routing index
loaded_when: Any PROC LOGISTIC / GLM / MIXED / GENMOD / LIFETEST / PHREG / SURVEY* task, or any modeling / survey-weighted analysis work.
---

## Routing Table

Load the atom matching the procedure in use. All atoms share one core
grammar: `CLASS` declares categorical predictors, `MODEL` specifies
fixed effects, and silent defaults for response ordering, link
function, and variance structure are almost always wrong for
claims-data work. Capture structured output via `ODS OUTPUT` — see the
ODS reference — because these procs do not return data to macros.

| Atom | Load when you see... | One-line summary |
|------|----------------------|------------------|
| `proc-logistic.md` | `PROC LOGISTIC`, binary/ordinal/nominal logistic regression, odds ratios | Default models `P(Y=lowest)`; pin event with `event='1'` or `descending`; reference coding via `CLASS ... / param=ref` |
| `proc-glm.md` | `PROC GLM`, ANOVA / ANCOVA / linear regression, Type III SS, LSMEANS | `CLASS` for categorical effects; Type III SS default; `SOLUTION` for parameter estimates; `LSMEANS` for covariate-adjusted marginal means |
| `proc-mixed.md` | `PROC MIXED`, random effects, repeated measures, `ddfm=kr` | `RANDOM` is G-side (random effects); `REPEATED` is R-side (residual correlation) — not interchangeable; use `ddfm=kr` for unbalanced panels |
| `proc-genmod.md` | `PROC GENMOD`, GLM family fits, Poisson / binomial / gamma, GEE | Default `DIST=NORMAL LINK=IDENTITY` is silent OLS; specify `DIST=` + `LINK=`; `REPEATED SUBJECT=` for GEE |
| `proc-lifetest.md` | `PROC LIFETEST`, Kaplan-Meier, log-rank, nonparametric survival | `TIME t*status(code)` — the parenthesized value is the CENSOR code, not the event; `STRATA` produces per-group curves + log-rank test |
| `proc-phreg.md` | `PROC PHREG`, Cox proportional hazards, hazard ratios | Same `TIME` censor-code pitfall as LIFETEST; `HAZARDRATIO` for per-covariate HR with CIs; `CLASS ... / param=ref` needed for categorical predictors |
| `proc-surveymeans.md` | `PROC SURVEYMEANS` / `SURVEYFREQ` / `SURVEYLOGISTIC` / `SURVEYREG`, NHANES / BRFSS / MEPS | Design variables `STRATA` / `CLUSTER` / `WEIGHT` are mandatory; omitting them silently assumes SRS and produces wrong SEs / CIs / p-values |

## Universal Rules (apply to all atoms)

- `CLASS` is required for every categorical predictor — numeric
  categoricals omitted from `CLASS` are silently treated as continuous.
- None of these procs return data to macros — use `ODS OUTPUT
  <TableName>=<outds>` to capture `ParameterEstimates`, `OddsRatios`,
  `LSMeans`, `ModelFit`, etc. Table names are case-sensitive.
- `LSMEANS` produces covariate-adjusted (marginal) means, NOT
  arithmetic means. Use `PROC MEANS` for raw descriptive means.

## Sibling cross-references

- DATA-step preprocessing (recoding, survival-time construction) —
  `../data-step/retain-pdv.md`, `../data-step/where-vs-if.md`.
- Analysis-dataset building via SQL joins — see the PROC SQL reference.
- Descriptive categorical / numeric summaries — `../base-procs/proc-freq.md`,
  `../base-procs/proc-means.md`, `../base-procs/proc-univariate.md`.
- ODS OUTPUT routing and capture — see the ODS reference.
