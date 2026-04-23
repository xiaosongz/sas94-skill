---
title: macro debugging switches and symbol-table inspection
loaded_when: 'macro returns wrong value / no value; resolution-order bug suspected; need to see generated DATA/PROC code; compile-only dry run; dumping macro symbol table with `%PUT _USER_` / `%PUT _ALL_`.'
---

## Critical Rules

### Rule 7: Macro debugging — toggle `MPRINT` / `MLOGIC` / `SYMBOLGEN` locally; inspect symbol tables with `%PUT _USER_` / `%PUT _ALL_`

Macro-side silent failures are almost always resolution-order bugs, and
the log by default shows only the generated code — not how it was
generated. Three `OPTIONS` switches reveal the missing half:

- `MPRINT` prints the DATA/PROC code the macro generates.
- `MLOGIC` prints the branch the macro took (`%if` results, `%do` loop
  boundaries).
- `SYMBOLGEN` prints every `&var` resolution.

Turn them on around the suspect block, then turn them off — leaving them
on in production pollutes the log and slows large jobs. For symbol-table
inspection, `%PUT _USER_` lists every user-defined macro variable in
scope; `%PUT _ALL_` adds the automatic ones (`&SYSDATE9`, `&SYSUSERID`,
...). `OPTIONS OBS=0` lets a DATA step compile without reading any rows
— useful for a syntax-only dry run of macro-generated code.

```sas
/* CORRECT - scope the debug switches tightly */
options mprint mlogic symbolgen;
%my_suspect_macro(claims, 2024)
options nomprint nomlogic nosymbolgen;

/* CORRECT - dump the user-defined symbol table */
%put _USER_;            /* user-defined macro vars only */
%put _ALL_;             /* + &SYSDATE9 / &SYSUSERID / &SYSMACRONAME / ... */

/* CORRECT - compile-only dry run of macro-generated DATA steps */
options obs=0 nonotes nosource;
%run_pipeline(2024)
options obs=max notes source;
```

```sas
/* WRONG - leaving the debug switches on for the whole session */
options mprint mlogic symbolgen;       /* never turned off */
/* log becomes unreadable; every &var and every branch dumps into it */
```

## Function / Statement Quick Ref

| Name | Syntax | Purpose | Common mistake |
|------|--------|---------|----------------|
| `OPTIONS MPRINT` | `options mprint;` / `options nomprint;` | Log the generated DATA / PROC code | Leaving on in production — log floods |
| `OPTIONS MLOGIC` | `options mlogic;` / `options nomlogic;` | Log macro branching / `%if` / `%do` | Same — log-flood risk on long runs |
| `OPTIONS SYMBOLGEN` | `options symbolgen;` / `options nosymbolgen;` | Log every `&var` resolution | Dumping entire symbol tables on long runs |
| `OPTIONS OBS=0` | `options obs=0;` / `options obs=max;` | Compile-only dry run — read 0 rows | Forgetting to reset → downstream steps see empty data |
| `OPTIONS NONOTES` | `options nonotes;` / `options notes;` | Suppress NOTE: lines in dry-run logs | Leaving off — real NOTEs get lost |
| `OPTIONS NOSOURCE` | `options nosource;` / `options source;` | Suppress echo of submitted source | Same — makes errors harder to locate |
| `%put _USER_` | `%put _USER_;` | List user-defined macro variables in scope | Using on its own to "see everything" — need `_ALL_` |
| `%put _ALL_` | `%put _ALL_;` | List user + automatic macro variables | Including `&SYSPBUFF` etc. — noisy on release logs |

## Silent Pitfalls

- **Debug `OPTIONS` left on in production** — `MPRINT` / `MLOGIC` /
  `SYMBOLGEN` each multiply log volume per macro call; leaving them on
  a long batch run fills the log with generated source, branch traces,
  and every `&var` resolution. Always reset with the matching `NO...`
  option after the debug block.

- **`OPTIONS OBS=0` left on after the dry run** — every downstream
  DATA/PROC step silently reads zero rows. Pair every `obs=0` with a
  matching `obs=max` at the close of the dry-run block.

- **`%put _USER_` in a call-site context expecting to see an inner
  macro's locals** — once the inner macro `%mend`s, its locals are gone.
  Put the `%put _USER_` *inside* the macro (before the `%mend`) if you
  need the inner scope.

- **Reading the log for `MPRINT` output but running in a mode where
  `MPRINT` was never enabled** — `MPRINT` must be on *before* the macro
  call; toggling after resolves the same code with no generation trace.

## Anti-patterns (STOP signs)

- `options mprint mlogic symbolgen;` at the top of a program with no
  matching `options nomprint nomlogic nosymbolgen;` → log-flood.
- `options obs=0;` without a matching `options obs=max;` before the
  real pipeline runs → silent zero-row outputs.
- Debugging a macro by adding `%put` statements to production code and
  leaving them in — prefer `MPRINT` / `SYMBOLGEN` toggled around the
  call, or `%put _USER_;` inside the macro guarded by a `debug=` param.
