---
title: PROC SQL INTO :macvar and dynamic-SQL list building
loaded_when: '"INTO :", "SEPARATED BY", "INTO :list1-:listN", building IN() lists from SQL, dynamic SQL column-list generation, dictionary.columns-based codegen, "macro variable from SQL", NOTRIM/TRIM issues.'
---

## Critical Rules

### Rule 4: `INTO :macvar SEPARATED BY ','` needs `%trim` / `strip()` before going into an `IN()` clause

`SELECT DISTINCT col INTO :list SEPARATED BY ','` pads the macro
variable to the SQL query's working width. Passing `&list` directly into
a downstream `IN(&list)` works for numerics but fails silently for short
character codes — trailing blanks inside the list cause the `IN` to miss
matches. Always `%let list = %trim(&list);` or `strip()` each element.

```sas
/* CORRECT - bound and trim the list, then use in a downstream query */
proc sql noprint;
  select distinct quote(strip(dx_code))
    into :dx_list separated by ','
  from priority_codes;
quit;
%let dx_list = %sysfunc(compbl(&dx_list));

proc sql;
  create table hits as
  select * from claims where dx_code in (&dx_list);
quit;
```

```sas
/* WRONG - blank-padded codes in the IN() silently miss matches */
proc sql noprint;
  select distinct dx_code
    into :dx_list separated by ','
  from priority_codes;
quit;

proc sql;
  create table hits as
  select * from claims where dx_code in (&dx_list);
quit;
```

## Canonical Idiom: `INTO :list SEPARATED BY ' '` for dynamic column lists

Read `dictionary.columns` to build a dynamic column list, then paste it
into a generated SELECT / VAR statement. Common pattern for "select
every numeric variable except the key" style queries.

```sas
proc sql noprint;
  select name
    into :num_vars separated by ' '
  from dictionary.columns
  where libname = 'WORK'
    and memname = 'CLAIMS'
    and type = 'num'
    and upcase(name) ne 'MEMBER_ID';
quit;

proc means data=claims noprint;
  class member_id;
  var &num_vars;
  output out=claims_summary sum= / autoname;
run;
```

## Canonical Idiom: Dictionary-table introspection

Programmatic schema lookup for generated code or audit. Avoids
hand-maintaining a list of variable names across pipeline stages.

```sas
proc sql;
  create table work_schema as
  select libname, memname, name, type, length, label
  from dictionary.columns
  where libname = 'WORK'
  order by memname, name;
quit;
```

## INTO-target forms

| Form | Purpose |
|------|---------|
| `into :mv` | Scalar — first row's value of the selected column |
| `into :mv1 - :mvN` | Indexed list — one macvar per row (up to N) |
| `into :mv separated by ','` | Delimited scalar — every row joined with the delimiter |
| `into :mv separated by ',' notrim` | Same, but preserve per-element padding (rarely what you want) |

Pair with `NOPRINT` on the `proc sql` statement to suppress the result
window output, otherwise the scalar / list also prints.

## Quick Ref

| Name | Syntax | Purpose | Common mistake |
|------|--------|---------|----------------|
| `INTO :mv` | `select col into :mv from t;` | Write a scalar into a macro variable | Forgetting `NOPRINT` on the PROC SQL |
| `INTO :mv SEPARATED BY` | `select col into :mv separated by ',' from t;` | Build a delimited list macro var | Not trimming before pasting into `IN()` (Rule 4) |
| `DICTIONARY.COLUMNS` | `select ... from dictionary.columns where libname='...'` | Schema introspection | Using `sashelp.vcolumn` (view over the same) in PROC SQL — fine, but slower |

## Silent Pitfalls

- **`INTO :list` trailing blanks** — character-list macvars pick up
  blank padding from the longest element's storage length, not the
  visible content. Downstream `IN(&list)` misses matches for shorter
  codes. Always strip / trim before use (Rule 4).
- **Scalar `INTO :mv` with multi-row result** — silently takes the first
  row only; add `DISTINCT` or an aggregate to make the intent explicit.
- **Forgotten `NOPRINT`** — the values print to the results window,
  cluttering logs and interactive sessions.

## Anti-patterns

- `select ... into :list separated by ','` from a character source with
  no `strip()` / `%trim`, then `where col in (&list)` → Rule 4.
- Hand-maintaining a variable-name list that lives in both the DATA
  step and a downstream MEANS / SUMMARY call, when
  `dictionary.columns` + `INTO :list` would keep them in sync.

Consumer-side macro-variable references, quoting, and dequoting live in
`../macros/scope-and-quoting.md` and `../macros/sysfunc-and-eval.md`.
