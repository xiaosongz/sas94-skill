---
title: ODS SELECT / ODS EXCLUDE
loaded_when: '"ODS SELECT", "ODS EXCLUDE", "narrow rtf to one table", "suppress fitstatistics from pdf", "filter proc output tables", "persist=proc", or any task that filters which PROC output objects reach a destination.'
---

## Critical Rules

### Rule: `ODS SELECT` / `ODS EXCLUDE` controls which output objects a destination receives — default is SELECT ALL for everything except the OUTPUT destination

Every open destination maintains a selection list. The default is
`SELECT ALL` for RTF / EXCEL / PDF / HTML / LISTING — every output
object the proc emits goes through. The OUTPUT destination starts
at `EXCLUDE ALL` — nothing becomes a dataset until you name it via
`ODS OUTPUT ...`. To gate a destination to a single table, use
`ods rtf select ParameterEstimates;` before the proc; list resets
at the next PROC step unless you add `PERSIST=PROC`.

```sas
/* CORRECT - RTF gets only the ParameterEstimates table */
ods rtf file="lr_params.rtf";
ods rtf select ParameterEstimates;
proc logistic data=claims; model outcome = age sex; run;
ods rtf close;
```

```sas
/* WRONG - RTF gets every default panel; the file is 40 pages */
ods rtf file="lr_params.rtf";
proc logistic data=claims; model outcome = age sex; run;
ods rtf close;
```

## Canonical Idioms

### Narrow a destination to a single output object

Use `ODS dest SELECT name;` before the PROC. Without `PERSIST=`,
the selection applies only to the next PROC step; the list then
reverts to `SELECT ALL`. For multi-PROC persistence, add
`PERSIST=PROC`.

```sas
ods rtf file="pe_only.rtf" style=journal;
ods rtf select ParameterEstimates;
proc logistic data=claims; model outcome = age sex; run;

/* selection already reverted - this PROC emits everything */
proc means data=claims; var paid_amt; run;
ods rtf close;
```

### Suppress one noisy object across multiple PROCs

Use `ODS dest EXCLUDE name / PERSIST=PROC;` to keep the rule active
across subsequent PROCs in the same destination scope. Typical use:
suppress `FitStatistics` from a slim modeling report.

```sas
ods rtf file="slim_models.rtf" style=journal;
ods rtf exclude FitStatistics / persist=proc;

proc logistic data=claims; model outcome = age sex;    run;
proc logistic data=claims; model outcome = age region; run;
proc logistic data=claims; model outcome = age plan;   run;

ods rtf close;
```

## Quick Ref

| Name | Syntax | Purpose | Common mistake |
|------|--------|---------|----------------|
| `ODS SELECT` | `ods rtf select ParameterEstimates;` | Narrow a destination's output list | Scope ends at next PROC unless `PERSIST=PROC` |
| `ODS EXCLUDE` | `ods rtf exclude FitStatistics;` | Suppress one or more objects for a destination | Same scope caveat as SELECT |
| `PERSIST=PROC` | `ods rtf select ... / persist=proc;` | Keep selection across subsequent PROCs | Forgetting, then only the first PROC is filtered |

## Silent Pitfalls

- **Scope reset at next PROC** — `ODS RTF SELECT X;` applies only
  to the next PROC step. Multi-PROC scripts need `PERSIST=PROC` or
  the filter evaporates silently.
- **Wrong destination name in SELECT/EXCLUDE** — `ods rtf select X;`
  only affects the RTF destination; the same PROC's output still
  goes to any other open destination (LISTING, PDF, ...) in full.
- **Object-name typo** — misspelled object name means the filter
  matches nothing; the destination receives the default `SELECT ALL`
  output with no warning.

## Anti-patterns

- Opening RTF for a single-table report but omitting `ODS RTF SELECT`,
  then producing a 40-page file with every default panel.
- Expecting one `ODS dest SELECT` before three PROCs to filter all
  three — without `PERSIST=PROC`, only the first PROC is filtered.

For the `ODS OUTPUT` destination's inverse default (`EXCLUDE ALL`), see `ods-output-capture.md`.
