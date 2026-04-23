---
title: PROC FREQ — counts, cross-tabs, OUT= idiom
loaded_when: '"PROC FREQ", "TABLES", "cross-tab", "crosstab", "frequency table", "MISSING option", "MISSPRINT", "one-way frequencies", "small-cell suppression", or "OUT= with freq".'
---

## Critical Rules

### Rule 1: `PROC FREQ TABLES a*b;` drops rows with missing in `a` or `b` by default — add `/ MISSING` to count them

The default `TABLES` behavior excludes observations with a missing
value on any table variable from both the cell counts and the
percent-of-total denominator. For claims-data prevalence calculations
this silently understates the denominator. Add `/ MISSING` to treat
missing as a category, or `/ MISSPRINT` to display (but not count)
missings.

```sas
/* CORRECT - explicit: missing counted as a category */
proc freq data=claims;
  tables dx_code * plan_type / missing;
run;
```

```sas
/* WRONG - silently drops claims with missing plan_type from denominator */
proc freq data=claims;
  tables dx_code * plan_type;
run;
```

## Canonical Idiom: minimum-count filter via `OUT=` + `WHERE=`

Purpose: generate a frequency table, keep only values with ≥ N
occurrences — common for privacy / small-cell-suppression filters and
for "what are the top dx codes" exploration.

```sas
proc freq data=claims noprint;
  tables dx_code / out=dx_freq(where=(count >= 10));
run;

proc sort data=dx_freq;
  by descending count;
run;
```

## Quick Ref

| Option / syntax | Purpose | Common mistake |
|-----------------|---------|----------------|
| `tables a*b;` | One-way / cross-tab counts | Default drops missing from cells and denominator |
| `tables a / missing` | Treat missing as a category | Forgetting → silent under-count |
| `tables a / misprint` | Display missing, don't count | Confused with `missing` |
| `tables x / out=ds` | Write frequencies to a dataset | Omitting `noprint` on PROC → still prints |
| `noprint` (PROC option) | Suppress the printed table | Writing `noprint` on the TABLES statement instead |

## Anti-patterns (STOP signs)

- `proc freq; tables a*b; run;` with missing-bearing `a` or `b` →
  denominators silently exclude missings. Use `/ MISSING`.
