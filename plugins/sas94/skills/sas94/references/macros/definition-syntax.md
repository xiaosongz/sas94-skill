---
title: macro definition syntax (lint rules 1-6)
loaded_when: 'authoring or editing a `%macro` definition — signature parens, `%mend` name, nesting, parameter names, Doxygen header, `SECURE`/`STORE SOURCE` options.'
---

## Critical Rules

### Rule 1: Every `%macro` signature must carry parentheses `()`

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

Keep call sites readable — required inputs are positional (same order
every call), optional behavior flags are keyword-with-default. This is
the default shape across `sasjs/core` base macros.

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

Register the macro in a stored-compiled-macro catalog when `SASAUTOS` /
`MSTORED` is set. Placing the option on the same line as the closing `)`
keeps the signature compact and greppable.

```sas
%macro mf_abort(mac=mf_abort.sas, msg=, iftrue=%str(1=1)
)/des='ungraceful abort' /*STORE SOURCE*/;

  %if not(%eval(%unquote(&iftrue))) %then %return;
  %put NOTE: /// mf_abort macro executing //;
  %abort;

%mend mf_abort;
```

## Function / Statement Quick Ref

| Name | Syntax | Purpose | Common mistake |
|------|--------|---------|----------------|
| `%macro` | `%macro name(pos, kw=default) / options;` | Open a macro definition | Missing `()` in signature |
| `%mend` | `%mend name;` | Close a macro definition | Bare `%mend;` without name |
| `%let` | `%let var = value;` | Assign a macro variable | Forgetting scope — writes to outermost-matching scope |
| `%global` | `%global var1 var2;` | Declare a macro variable in the global symbol table | Declaring `%global` inside a macro that already has `%local var` |
| `%local` | `%local var1 var2;` | Declare variables local to the current macro | Forgetting `%local` — variable leaks to caller scope (see [scope-and-quoting.md](scope-and-quoting.md)) |

## Silent Pitfalls

- **Nested `%macro` compiles on every outer call** — the inner `%macro`
  statement is re-executed each time the outer macro runs, which is almost
  never the intent; `sasjs/lint noNestedMacros` flags it.

- **Encoded-password literals (`{SAS001}`, `{SAS002}`, `{SASENC}`) in
  source** — trivially reversible; `sasjs/lint noEncodedPasswords` flags
  any line containing `{SAS001}` / `{SAS002}` / `{SASENC}`. Prefer `SECURE`
  macros that read credentials from environment / authinfo.

- **"Gremlin" non-printable characters in a macro signature or parameter
  default** — invisible on screen, break string compares at runtime.
  `sasjs/lint noGremlins` flags non-allowed-list non-printables.

## Anti-patterns (STOP signs)

- `%macro foo; ... %mend;` without `()` → call-site bugs; see Rule 1.
- `%macro ...; %macro ...; %mend; %mend;` (nested) → see Rule 3.
- Bare `%mend;` with no name → see Rule 2.
- `%macro foo(var 1) /minXoperator;` → see Rule 4.
- `.sas` file with no `/** ... **/` header → see Rule 5.
- `%macro foo() / SE CURE;` or a credential-handling macro missing
  `SECURE` / `STORE SOURCE` → see Rule 6.
