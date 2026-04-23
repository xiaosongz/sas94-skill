---
title: PROC LIFETEST rules
loaded_when: PROC LIFETEST, Kaplan-Meier estimator, log-rank test, nonparametric survival / time-to-event analysis, `TIME t*status(code)` syntax, STRATA by group.
---

## Critical Rules

### Rule 5: LIFETEST `TIME t*status(code)` — the value in parentheses is the CENSORED code, not the event code

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

## Canonical Idioms

### Idiom: Kaplan-Meier survival curve by treatment with log-rank test

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

## Quick Ref

| Name | Syntax | Purpose | Common mistake |
|------|--------|---------|----------------|
| `PROC LIFETEST` | `proc lifetest; time t*c(0); strata g;` | Nonparametric survival (K-M) | `time t*c(1)` flipping the censor code (Rule 5) |
| `TIME time*status(c)` | `time days*event(0);` | Declare survival time + CENSOR code | Value in parens is CENSORED, not event |
| `STRATA` | `strata treatment;` | Per-group K-M curves + log-rank test | Too many strata → thin, noisy curves |
| `plots=survival(atrisk)` | `plots=survival(atrisk cb=hw);` | K-M plot with at-risk table / CIs | Omitting — reviewers want at-risk table |
| `ODS OUTPUT` | `ods output HomTests=lr ProductLimitEstimates=ple;` | Capture log-rank / survival estimates | Wrong table name → empty dataset |

## Silent Pitfalls

- **Inverted LIFETEST censor code** — `time days*event(1)` when 1
  is the event (not censoring) marks every event observation as
  censored. Survival curves look artificially high; log-rank tests
  are nonsense. See Rule 5.
- **Too many STRATA levels** — stratifying on a high-cardinality
  variable produces very thin per-group curves; the log-rank test
  loses power and plots become unreadable.
- **No at-risk table** — without `plots=survival(atrisk)` the
  reader cannot judge late-time instability. Standard reviewer ask.

## Anti-patterns

- `time days*event(1);` with `event` coded 0=censor 1=event → see
  Rule 5. Inverted censor code; every event censored.
- Using LIFETEST when you need covariate adjustment → move to
  `proc-phreg.md` (Cox model).
- Reporting the log-rank p-value alone without a survival curve or
  at-risk table → the test tells you almost nothing on its own.
