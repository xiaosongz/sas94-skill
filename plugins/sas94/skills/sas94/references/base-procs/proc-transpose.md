---
title: PROC TRANSPOSE — VAR default drops char
loaded_when: '"PROC TRANSPOSE", "long to wide", "wide to long", "pivot", "reshape", "ID statement", "PREFIX=", "_NAME_ _LABEL_", or "character columns dropped".'
---

## Critical Rules

### Rule 5: `PROC TRANSPOSE` with no `VAR` transposes every numeric variable — and silently drops every character

With no `VAR` statement, PROC TRANSPOSE transposes the `_NUMERIC_`
variables (excluding BY / ID / COPY vars) and writes no warning about
any character variables it skipped. For mixed-type input datasets
always specify `VAR` explicitly — both to document intent and to
surface a misspelled column name as a syntax error.

```sas
/* CORRECT - explicit VAR list */
proc transpose data=claims_long out=claims_wide prefix=paid_;
  by member_id;
  id visit_seq;
  var paid_amt;
run;
```

```sas
/* WRONG - no VAR; every numeric gets transposed, no warning about dropped chars */
proc transpose data=claims_long out=claims_wide prefix=v_;
  by member_id;
  id visit_seq;
run;
```

## Canonical Idiom: long → wide by `ID`

Purpose: pivot long-format visit records into one row per `member_id`
with columns `paid_1`, `paid_2`, ..., `paid_N`. The `ID` variable's
values become column-name suffixes; `PREFIX=` controls the stem.

```sas
proc sort data=claims_long;
  by member_id visit_seq;
run;

proc transpose data=claims_long
               out=claims_wide(drop=_name_)
               prefix=paid_;
  by member_id;
  id visit_seq;
  var paid_amt;
run;
```

## Quick Ref

| Statement / option | Purpose | Common mistake |
|--------------------|---------|----------------|
| `by g;` | One output row per BY group | Input must be sorted by `g` |
| `id seq;` | Use `seq` values as output column suffixes | Non-unique within BY → error |
| `var x;` | Columns to transpose | Omitting → chars silently dropped |
| `prefix=p_` | Stem for generated column names | Without it → raw ID values as names |
| `out=b(drop=_name_)` | Suppress `_NAME_` bookkeeping col | Leaving in → clutter downstream |

## Anti-patterns (STOP signs)

- `proc transpose data=mixed out=wide; by g; id seq; run;` with no
  `VAR` → character columns silently dropped.
