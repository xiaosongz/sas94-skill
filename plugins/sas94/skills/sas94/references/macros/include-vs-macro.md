---
title: '%INCLUDE vs %MACRO vs SET — when to use which'
loaded_when: 'deciding between file inclusion (`%INCLUDE`) and parameterized reuse (`%MACRO`); confusion between DATA-step `SET` and code-level inclusion; autoexec / libname / format-catalog config.'
---

## Critical Rules

### Rule 8: Use `%INCLUDE` for file-level composition; `%MACRO` for call-site reuse; `SET` for dataset merging — they are not interchangeable

`%INCLUDE '<path>';` inlines the contents of a file into the current
program at parse time — every `%let`, `%macro`, and global statement in
the included file is executed in the including program's scope. Use it
for shared config (autoexec fragments, libname blocks, format catalogs).

**Do not** use it as a substitute for `%MACRO` — a call-site `%INCLUDE
'some_step.sas';` has no parameter list, no local scope, and re-parses
the file on every invocation. For parameterized reusable logic, wrap
the file in `%macro name(...) / STORE SOURCE;` and call it.

`SET` is a DATA-step statement for combining datasets by stacking /
reading observations; it is not a code-inclusion mechanism.

```sas
/* CORRECT - %INCLUDE for one-time config at program head */
%include '/projects/study_2024/config/libnames.sas';
%include '/projects/study_2024/config/formats.sas';
/* now proceed with the analysis */

/* CORRECT - %macro for parameterized reuse */
%macro build_cohort(year=, dx_filter=) / STORE SOURCE;
  /* body */
%mend build_cohort;

%build_cohort(year=2023, dx_filter=E11)
%build_cohort(year=2024, dx_filter=E11)
```

```sas
/* WRONG - %INCLUDE used as pseudo-macro; no params, no scope, reparsed each call */
%include '/projects/study_2024/steps/build_cohort.sas';   /* runs once */
%include '/projects/study_2024/steps/build_cohort.sas';   /* re-parses the whole file, same vars */
```

### Decision summary

| Need | Use | Why |
|------|-----|-----|
| Load shared libname / format / option block once at program head | `%INCLUDE` | File-level composition; executes in caller scope at parse time. |
| Reusable logic with parameters (year, cohort, filter) | `%MACRO ... %MEND` | Parameter list, local scope, `/STORE SOURCE` for catalog reuse. |
| Stack or read observations from a dataset | DATA-step `SET` | This is dataset combining, not code composition. |

## Function / Statement Quick Ref

| Name | Syntax | Purpose | Common mistake |
|------|--------|---------|----------------|
| `%include` | `%include '/path/file.sas';` | Inline a source file at parse time into caller scope | Using in place of `%macro` for parameterized reuse |
| `%macro` / `%mend` | `%macro name(...) / STORE SOURCE; ... %mend name;` | Parameterized, scoped, catalog-storable reuse | Substituting with `%include` and losing parameters + scope |
| `SET` (DATA step) | `set lib.ds1 lib.ds2;` | Stack / read rows from dataset(s) | Confusing with code inclusion — `SET` does not read `.sas` files |

## Silent Pitfalls

- **`%INCLUDE` used as a pseudo-macro** — `%INCLUDE` has no parameters
  and no local scope. Every symbol the included file defines becomes
  live in the caller's scope at parse time. Re-running an include file
  to "call again with new args" does not work; the second `%INCLUDE`
  re-parses the same hard-coded values.

- **`%INCLUDE` of a file that itself contains `%let` / `%macro` /
  `libname` statements** — every one of those runs in the caller's
  scope. A stray `%let year=2023;` inside an innocuously-named config
  file will silently shadow the caller's `year` macro variable.

- **Relative paths in `%INCLUDE`** — resolution depends on the SAS
  working directory at submit time, not the file's own location. Prefer
  absolute paths or paths relative to a known `SAS_ROOT` macro variable.

- **`SET` confused with include** — `SET lib.ds;` reads rows from a
  dataset into the DATA step's PDV; it does not execute `.sas` code
  from a file.

## Anti-patterns (STOP signs)

- `%include '/path/step.sas'; %include '/path/step.sas';` expecting the
  second call to act like a fresh macro invocation → wrap the file in
  `%macro` instead.
- `%include '/path/build_cohort.sas';` where the file hard-codes
  `year=2023` and the caller wants a different year → convert to a
  `%macro build_cohort(year=)` with parameters.
- `set '/path/file.sas';` — this is a type confusion; `SET` takes
  dataset names, not file paths. Use `%include` for code or `infile`
  for external data.

Cross-ref: `../data-step/file-hygiene.md` covers the DATA-step-side
concerns for program-head config fragments (autoexec, libname blocks).
