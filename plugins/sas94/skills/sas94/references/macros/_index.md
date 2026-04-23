---
title: macros topic index
loaded_when: '"%macro", "%let", "%sysfunc", quoting error, `&&var`, symget/symput, or any macro authoring/debugging task — load the specific atom for the sub-topic.'
---

## Routing Table

The SAS macro language runs at compile time — it generates SAS code that
then executes. Most "macro errors" are actually *resolution-order* errors:
the macro processor resolved something too early, too late, or in the
wrong scope. This topic is split into six atoms; load only what the task
needs.

| Atom | Load when |
|------|-----------|
| [definition-syntax.md](definition-syntax.md) | Authoring a `%macro`; lint rules 1-6 (parens, `%mend` name, no nesting, strict definition, Doxygen header, `SECURE`/`STORE`); `%macro` / `%mend` / `%let` / `%global` / `%local` Quick Ref. |
| [scope-and-quoting.md](scope-and-quoting.md) | Scope leak (`%let` inside `%macro` without `%local`); quoting bugs (`%str`, `%nrstr`, `%bquote`, `%nrbquote`, `%superq`); `call symputx` / `symget` scope argument. |
| [debugging.md](debugging.md) | Macro returns wrong value, log too quiet, resolution-order suspected; toggling `MPRINT` / `MLOGIC` / `SYMBOLGEN`; `%PUT _USER_` / `%PUT _ALL_`; `OPTIONS OBS=0 NONOTES NOSOURCE` dry run. |
| [include-vs-macro.md](include-vs-macro.md) | Deciding between `%INCLUDE`, `%MACRO`, and DATA-step `SET`; file inclusion at parse time vs parameterized reuse. |
| [sysfunc-and-eval.md](sysfunc-and-eval.md) | Arithmetic inside macro code; calling DATA-step functions from macro context; `%eval` integer-only vs `%sysevalf` floating with `integer` / `ceil` / `floor` / `boolean` conversion. |

## Cross-topic siblings

- `../data-step/macro-quoting.md` — DATA-step-side of macro-generated code, `call symputx` / `symget`.
- `../data-step/file-hygiene.md` — program-head autoexec fragments that pair with `%INCLUDE`.
- `../base-procs/schema-utils.md` — `PROC SQL INTO :macvar` list pattern (loaded separately).
