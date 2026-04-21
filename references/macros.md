---
title: SAS macro language reference
scope: '`%let`, `%macro` scope, quoting functions (`%str`, `%nrstr`, `%bquote`, `%superq`), `&&var` resolution, `call symput` / `symget()`.'
loaded_when: '"%macro", "%let", "%sysfunc", quoting error, `&&var`, symget/symput, or any macro authoring or debugging task.'
last_reviewed: 2026-04-21
reviewer: xiaosongz
---

## Overview

The SAS macro language runs at compile time — it generates SAS code that
then executes. Most "macro errors" are actually *resolution-order* errors:
the macro processor resolved something too early, too late, or in the
wrong scope. This file encodes the definition and scope rules from
`sasjs/lint` (15-rule v2.4.3 ruleset) and the idiomatic patterns from
`sasjs/core` (v4.63.0, ~150 Doxygen-headed base macros) so that generated
macro code is well-formed by construction.

## Critical Rules

### Rule 1: Every `%macro` signature must carry parentheses `()`

Source: https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/file/hasMacroParentheses.ts

Without `()`, `sasjs/lint hasMacroParentheses` fires. The `()` form is a
`sasjs/core` convention that keeps the signature shape stable whether the
macro takes zero or many parameters, and it's the slot that
`/*/STORE SOURCE*/` and `/des=` idioms plug into.

```sas
/* CORRECT */
%macro somemacro();
  %put &sysmacroname;
%mend somemacro;
```

```sas
/* WRONG - missing parentheses; sasjs/lint hasMacroParentheses fires */
%macro somemacro;
  %put &sysmacroname;
%mend somemacro;
```

### Rule 2: Close every `%mend` with its macro name

Source: https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/file/hasMacroNameInMend.ts

`%mend;` (name-less) is legal SAS but ambiguous when macros are long,
nested, or edited across hands. `sasjs/lint hasMacroNameInMend` requires
`%mend <name>;` matching the `%macro <name>` signature.

```sas
/* CORRECT */
%macro somemacro();
  %put &sysmacroname;
%mend somemacro;
```

```sas
/* WRONG - bare %mend; hasMacroNameInMend fires */
%macro somemacro();
  %put &sysmacroname;
%mend;
```

### Rule 3: No nested `%macro` definitions

Source: https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/file/noNestedMacros.ts

A `%macro` defined inside another `%macro` recompiles on every outer-macro
call — slow, hard to debug, and prevents `/STORE SOURCE` reuse. `sasjs/lint
noNestedMacros` flags any `%macro` inside a `%macro ... %mend` pair.

```sas
/* CORRECT - define inner separately, call it from outer */
%macro inner();
  %put inner;
%mend inner;

%macro outer();
  %inner()
  %put outer;
%mend outer;
```

```sas
/* WRONG - inner nested inside outer; noNestedMacros fires */
%macro outer();
  %macro inner();
    %put inner;
  %mend inner;
  %inner()
%mend outer;
```

### Rule 4: Strict macro-definition syntax — no spaces inside parameter names or invalid options

Source: https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/file/strictMacroDefinition.ts

`sasjs/lint strictMacroDefinition` forbids spaces inside a parameter name
(`var 1` vs `var1`) and rejects unknown macro-statement options (only
`SECURE`, `SRC`, `STORE`, `DES=`, `MINOPERATOR`, `CMD` et al. are valid).

```sas
/* CORRECT */
%macro somemacro(var1, var2) /minoperator;
```

```sas
/* WRONG - space inside param name, invalid option */
%macro somemacro(var1, var 2) /minXoperator;
```

### Rule 5: Every macro file starts with a Doxygen header (`@file`, `@brief`, `@param`, `@version`, `@author`)

Source: https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/file/hasDoxygenHeader.ts

`sasjs/lint hasDoxygenHeader` requires a `/** ... **/` block as the first
non-blank content in every `.sas` file. The tags follow Doxygen
conventions; `sasjs/core` uses `@file`, `@brief`, `@details`, `@param [in]`,
`@param [out]`, `@return`, `@version`, `@author`.

```sas
/* CORRECT */
/**
  @file
  @brief Returns an unused libref
  @param [in] prefix= (mclib) Prefix for the libref name
  @version 9.2
  @author Allan Bowe
**/
%macro mf_getuniquelibref(prefix=mclib, maxtries=1000);
  %local x libref;
  /* body */
%mend mf_getuniquelibref;
```

```sas
/* WRONG - no header at file top; hasDoxygenHeader fires */
%macro mf_getuniquelibref(prefix=mclib, maxtries=1000);
  %local x libref;
%mend mf_getuniquelibref;
```

### Rule 6: Macros that are shared, stored, or security-sensitive carry required options (`SECURE`, `STORE SOURCE`)

Source: https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/file/hasRequiredMacroOptions.ts

`sasjs/lint hasRequiredMacroOptions` enforces a project-configured list of
mandatory options after the `/` in a `%macro` definition. Typical values
are `SECURE` (for credential-handling macros) and `STORE SOURCE` (for
stored-compiled-macro reuse). The options are whitespace-sensitive: `SE
CURE` is not the same as `SECURE`.

```sas
/* CORRECT */
%macro somemacro() / SECURE;
%macro another()  / SECURE SRC;
```

```sas
/* WRONG - SECURE split by whitespace; hasRequiredMacroOptions fires */
%macro somemacro(var1, var2) / SE CURE;
```

## Canonical Idioms

### Idiom: Positional-required + keyword-optional parameter pattern

Source: https://github.com/sasjs/core/blob/3a54b9c796c0bfe477d1aefc1e22b9ff9f2c96c2/base/mf_existds.sas

Purpose: keep macro call sites readable — required inputs are positional
(same order every call), optional behavior flags are keyword-with-default.
This is the default shape across `sasjs/core` base macros.

```sas
/* libds is positional-required; other args are keyword-optional */
%macro mf_existds(libds
)/*/STORE SOURCE*/;

  %if %sysfunc(exist(&libds)) ne 1 & %sysfunc(exist(&libds,VIEW)) ne 1
    %then 0;
  %else 1;

%mend mf_existds;
```

### Idiom: `/*/STORE SOURCE*/` inline option — one-line signature close

Source: https://github.com/sasjs/core/blob/3a54b9c796c0bfe477d1aefc1e22b9ff9f2c96c2/base/mf_abort.sas

Purpose: register the macro in a stored-compiled-macro catalog when
`SASAUTOS` / `MSTORED` is set. Placing the option on the same line as the
closing `)` keeps the signature compact and greppable.

```sas
%macro mf_abort(mac=mf_abort.sas, msg=, iftrue=%str(1=1)
)/des='ungraceful abort' /*STORE SOURCE*/;

  %if not(%eval(%unquote(&iftrue))) %then %return;
  %put NOTE: /// mf_abort macro executing //;
  %abort;

%mend mf_abort;
```

### Idiom: `%local` discipline — declare every non-parameter symbol at top

Source: https://github.com/sasjs/core/blob/3a54b9c796c0bfe477d1aefc1e22b9ff9f2c96c2/base/mp_hashdataset.sas

Purpose: prevent the macro from leaking variables into the outer / global
symbol table. Every local symbol the macro uses is declared `%local` once,
immediately after the `%macro` signature, before any logic.

```sas
%macro mp_hashdataset(libds, outds=work._data_, salt=, iftrue=%str(1=1)
)/*/STORE SOURCE*/;

  %local keyvar prevkeyvar lastvar cvars nvars;   /* declare everything upfront */

  %if not(%eval(%unquote(&iftrue))) %then %return;
  %let keyvar=%mf_getuniquename();
  %let prevkeyvar=%mf_getuniquename();
  /* body uses only &keyvar &prevkeyvar ... — nothing leaks */

%mend mp_hashdataset;
```

### Idiom: Guarded-execution `iftrue=` parameter

Source: https://github.com/sasjs/core/blob/3a54b9c796c0bfe477d1aefc1e22b9ff9f2c96c2/base/mp_hashdataset.sas

Purpose: allow the caller to suppress the macro's side effects with a
one-line predicate, without wrapping every call site in an outer `%if`.
The macro evaluates `iftrue` as a macro expression and `%return`s early
when false.

```sas
%macro mp_hashdataset(libds, outds=work._data_, iftrue=%str(1=1)
)/*/STORE SOURCE*/;
  %local ...;
  %if not(%eval(%unquote(&iftrue))) %then %return;
  /* real work */
%mend mp_hashdataset;
```

## Function / Statement Quick Ref

| Name | Syntax | Purpose | Common mistake | Doc URL |
|------|--------|---------|----------------|---------|
| `%macro` | `%macro name(pos, kw=default) / options;` | Open a macro definition | Missing `()` in signature | TODO (source pending) |
| `%mend` | `%mend name;` | Close a macro definition | Bare `%mend;` without name | TODO (source pending) |
| `%let` | `%let var = value;` | Assign a macro variable | Forgetting scope — writes to outermost-matching scope | TODO (source pending) |
| `%global` | `%global var1 var2;` | Declare a macro variable in the global symbol table | Declaring `%global` inside a macro that already has `%local var` | TODO (source pending) |
| `%local` | `%local var1 var2;` | Declare variables local to the current macro | Forgetting `%local` — variable leaks to caller scope | TODO (source pending) |
| `%do` / `%end` | `%do i = 1 %to 10; ... %end;` | Iterative macro loop | Using `&i` after `%end;` — value is last-iter value | TODO (source pending) |
| `%if` / `%then` / `%else` | `%if cond %then %do; ... %end; %else %do; ... %end;` | Conditional macro logic | Using DATA-step `if` vs macro `%if` | TODO (source pending) |
| `%put` | `%put NOTE- message;` | Write to the SAS log | Using `%put` without `NOTE-` / `WARNING-` / `ERROR-` tag | TODO (source pending) |
| `%sysfunc` | `%sysfunc(func(args), format)` | Call a DATA-step function from macro code | Forgetting the optional format argument | TODO (source pending) |
| `%str` | `%str(text with , ; = etc.)` | Mask special chars at compile time | Using `%str('text')` expecting `&var` to NOT resolve (still does) | TODO (source pending) |
| `%nrstr` | `%nrstr(&var literal)` | Mask `&` and `%` triggers at compile time | Omitting when passing a literal with `&var` through a parameter | TODO (source pending) |
| `%bquote` | `%bquote(&var with unbalanced quote)` | Mask special chars at macro-execution time | Using `%str` when unbalanced quotes require `%bquote` | TODO (source pending) |
| `%nrbquote` | `%nrbquote(&var with & or %)` | Mask `&`, `%`, and special chars at execution time | Picking wrong quote-function tier | TODO (source pending) |
| `%eval` | `%eval(&a + &b)` | Integer-only arithmetic in macro | Using on decimals — use `%sysevalf` | TODO (source pending) |
| `%sysevalf` | `%sysevalf(&a / &b, ceil)` | Floating-point arithmetic in macro | Omitting conversion type (`integer`, `ceil`, `floor`, `boolean`) | TODO (source pending) |
| `call symputx` | `call symputx('var', value, 'G'|'L'|'F');` | Write a macro variable from a DATA step | Omitting scope arg — defaults to most-local; surprises in nested contexts | TODO (source pending) |
| `symget` | `symget('var')` | Read a macro variable inside a DATA step | Using `symget` when compile-time `&var` would work | TODO (source pending) |

## Silent Pitfalls

- **`%let x = &y;` inside a macro without `%local x`** — writes `x` to the
  most-local existing scope; if `x` exists at an outer level, the outer `x`
  is overwritten. Declare `%local` for every non-parameter symbol (see
  "%local discipline" idiom above).
  Source: https://github.com/sasjs/core/blob/3a54b9c796c0bfe477d1aefc1e22b9ff9f2c96c2/base/mp_hashdataset.sas

- **Nested `%macro` compiles on every outer call** — the inner `%macro`
  statement is re-executed each time the outer macro runs, which is almost
  never the intent; `sasjs/lint noNestedMacros` flags it.
  Source: https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/file/noNestedMacros.ts

- **Encoded-password literals (`{SAS001}`, `{SAS002}`, `{SASENC}`) in
  source** — trivially reversible; `sasjs/lint noEncodedPasswords` flags
  any line containing `{SAS001}` / `{SAS002}` / `{SASENC}`.
  Source: https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/line/noEncodedPasswords.ts

- **"Gremlin" non-printable characters in a macro signature or parameter
  default** — invisible on screen, break string compares at runtime.
  `sasjs/lint noGremlins` flags non-allowed-list non-printables.
  Source: https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/line/noGremlins.ts

- **`'&var'` quote-suppression myth in macro context** — in DATA/PROC
  step string literals, single quotes keep `&var` literal while double
  quotes resolve it; in macro-context statements (`%put`, `%let`, `%if`),
  the macro processor scans for `&` and `%` triggers *before* the
  statement receives its argument, so quote type does not suppress
  resolution. `%put 'table: &name';` still resolves `&name` — the single
  quotes become literal output characters. Use `%nrstr(...)` or
  `%str(%&...)` to mask triggers in macro context. See GWU item 5.
  Source: `pipeline/manual/gwu-data-mining-5-items.md`.

## Anti-patterns (STOP signs)

**STOP** when you see any of the following — the code compiles but is
almost certainly wrong:

- `%macro foo; ... %mend;` without `()` → call-site bugs; see Rule 1.
- `%macro ...; %macro ...; %mend; %mend;` (nested) → see Rule 3.
- `%let x = &y;` inside a `%macro` with no `%local x;` → scope leak; see
  Silent Pitfalls.
- `%put 'text with &var';` expecting `&var` to stay literal → quotes in
  macro-context statements do NOT suppress resolution; the macro processor
  scans triggers before the statement sees its argument. Use `%nrstr(...)`
  to mask. See GWU item 5 in `pipeline/manual/gwu-data-mining-5-items.md`.
- Encoded-password literals `{SAS001}`, `{SAS002}`, `{SASENC}` in source →
  see Silent Pitfalls.

## See Also

- [sas-master-reference.md](sas-master-reference.md) — grammar and
  execution-model overview; top-20 rules aggregated from macros +
  data-step + GWU items.
- [data-step.md](data-step.md) — DATA-step-side of macro-generated code;
  `call symputx` / `symget` cross-reference.
- [proc-sql.md](proc-sql.md) — `INTO :macvar` list pattern (Phase 2+).
- [idioms-from-lexjansen.md](idioms-from-lexjansen.md) — deeper macro
  quoting treatments from SUGI papers (Phase 2+).
