---
title: Whitlock / Lepp macro-quoting idioms (NESUG 2009, PhUSE 2019)
loaded_when: "Whitlock macro quoting", "Lepp macro quoting", `%STR` vs `%NRSTR` vs `%BQUOTE` vs `%NRBQUOTE` vs `%SUPERQ`, compile-time vs execution-time quoting, `%NRSTR` + `%UNQUOTE` run-time macro object build, user-supplied values with embedded `&` / `%` / apostrophe.
---

## Critical Rules

### Rule: `%STR` / `%NRSTR` mask at compile time; `%BQUOTE` / `%NRBQUOTE` / `%SUPERQ` mask at execution time — pick by WHEN the offending symbol is seen, not by WHAT it is

Lepp's rule, restated: "To mask static text input use %STR or %NRSTR.
To mask the content of &macro variables or %macro calls use %BQUOTE,
%NRBQUOTE or %SUPERQ." The macro compiler reads your source code
once; if the problematic character (semicolon, ampersand, unbalanced
quote) is in the literal source, a compile-time quoter applies. If
the problematic character is inside a `&var` value that doesn't exist
until run time, only an execution-time quoter can see it. Picking the
wrong tier is the single most common "why isn't my macro quoting
working" root cause Whitlock and Lepp both diagnose. (Lepp, PhUSE
2019.)

```sas
/* CORRECT - compile-time semicolon in literal text -> %STR;
   execution-time apostrophe inside an unknown claimant name -> %BQUOTE */
%let stmt_end = %str(;);                     /* literal semicolon in source */
%let patient_name = O'Brien;                 /* stored with a bare apostrophe */
%put quoted: %bquote(&patient_name) ;        /* execution-time mask */
```

```sas
/* WRONG - %STR on a macro variable value; the apostrophe is invisible
   at compile time, so %STR has nothing to quote. Macro processor
   hits the unbalanced apostrophe at run time and errors. */
%let patient_name = O'Brien;
%put quoted: %str(&patient_name) ;
```

## Canonical Idioms

### Idiom: Whitlock `%NRSTR` + `%UNQUOTE` to build a macro object at run time

Whitlock's NESUG 2009 paper demonstrates a subtle two-step: `%NRSTR`
hides an ampersand from the macro compiler so no resolution decision
is made, then `%UNQUOTE` at execution time glues the ampersand to a
run-time-generated variable name, producing a reference the macro
facility evaluates. Useful when a variable name itself is built from
a macro call — rare in straightforward pipelines, critical in
code-generation macros that emit `%let &var = ...` targets where
`&var` is not known until run time. (Whitlock, NESUG 2009.)

```sas
/* Whitlock's NESUG 2009 paper uses bare `%macro makename;` (no parens).
   Parens added here to comply with sasjs/lint hasMacroParentheses;
   pattern is otherwise identical. */
%macro makename();
  claim_count_2024
%mend makename;

%macro set_and_read();
  %let %makename = 77;
  %put %unquote(%nrstr(&)%makename);   /* prints 77, not &claim_count_2024 */
%mend set_and_read;

%set_and_read
```

### Idiom: Lepp `%SUPERQ` for one-shot "freeze the value exactly" reads

Lepp identifies `%SUPERQ` as "the actual sister function to `%NRSTR`
at execution time" — it takes a macro variable *name* (no leading
`&`) and returns the value with every `&` and `%` trigger masked,
without attempting resolution. The right tool when a claimant name,
provider name, or operating-system path contains characters that
would otherwise fire warnings. Unlike `%BQUOTE`, `%SUPERQ` does not
resolve nested macro references inside the value first, which is the
desired behavior when the value is user-supplied data rather than
generated code. (Lepp, PhUSE 2019.)

```sas
%let ptname = O'Brien & Sons, %% discount;       /* nasty literal */

/* CORRECT - %SUPERQ freezes the exact stored value */
%put frozen: %superq(ptname) ;

/* CONTRAST - %BQUOTE would first try to resolve macro triggers and
   emit warnings about &Sons / %discount before masking. */
```

## Silent Pitfalls

- **Conflating `%BQUOTE` and `%SUPERQ`** — both are execution-time
  quoters, but `%BQUOTE(&var)` resolves nested references inside the
  value first, while `%SUPERQ(var)` (note: no ampersand) does not.
  Lepp's PhUSE paper is explicit that `%SUPERQ` is "the actual sister
  function to `%NRSTR` at execution time." For truly user-supplied
  data, `%SUPERQ` is safer.
- **`%STR` applied to a macro variable reference** — `%STR` is a
  compile-time directive; the resolution of `&var` happens later, so
  there is nothing for `%STR` to mask.

## Anti-patterns (STOP signs)

- `%str(&var)` where `&var` holds a quote character or ampersand —
  `%STR` is a compile-time directive; the resolution of `&var`
  happens later, so there is nothing for `%STR` to mask. Use
  `%BQUOTE(&var)` or `%SUPERQ(var)`.

Cross-refs: `../macros/scope-and-quoting.md`,
`../macros/sysfunc-and-eval.md`, `../data-step/macro-quoting.md`.
