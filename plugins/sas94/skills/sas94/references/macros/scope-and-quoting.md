---
title: macro scope and quoting functions
loaded_when: 'scope-leak suspected (`%let` inside a macro without `%local`); quoting error / unbalanced quote / literal `&` or `%`; `call symputx` / `symget` inside a DATA step; picking between `%str` / `%nrstr` / `%bquote` / `%nrbquote` / `%superq`.'
---

## Critical Rules

### Rule: Declare every non-parameter symbol with `%local` at the top of the macro

`%let x = &y;` inside a macro without `%local x;` writes `x` to the
most-local existing scope; if `x` exists at an outer level, the outer
`x` is overwritten. Declare `%local` for every non-parameter symbol
immediately after the `%macro` signature, before any logic.

```sas
/* CORRECT - every local symbol declared before use */
%macro mp_hashdataset(libds, outds=work._data_, salt=, iftrue=%str(1=1)
)/*/STORE SOURCE*/;

  %local keyvar prevkeyvar lastvar cvars nvars;   /* declare everything upfront */

  %if not(%eval(%unquote(&iftrue))) %then %return;
  %let keyvar=%mf_getuniquename();
  %let prevkeyvar=%mf_getuniquename();
  /* body uses only &keyvar &prevkeyvar ... — nothing leaks */

%mend mp_hashdataset;
```

```sas
/* WRONG - keyvar leaks to caller / global scope */
%macro mp_hashdataset(libds);
  %let keyvar = x_&libds;   /* no %local — overwrites outer keyvar if it exists */
%mend mp_hashdataset;
```

### Rule: Pick the right quoting function for the trigger you need to mask

Quoting functions mask macro triggers so the parser sees literal
characters. Two axes pick the tier:

1. **Compile-time vs execution-time.** `%str` / `%nrstr` mask at compile
   time (use when the string is a literal in the source). `%bquote` /
   `%nrbquote` / `%superq` mask at execution time (use when the string
   comes from `&var` and may contain unbalanced quotes or special
   chars).
2. **Mask `&` and `%` too?** The `nr` variants (`%nrstr`, `%nrbquote`)
   mask `&` and `%` as well — use when the literal contains a `&var`
   you want to keep literal, or a stray `%`.

`%superq(var)` is the strongest — it takes the name of a macro
variable (no `&`) and returns its unresolved value, masking every
trigger including `&` and `%`. Use when `&var` has content you cannot
predict (user input, URL-encoded strings, etc.).

```sas
/* CORRECT - compile-time mask of comma / semicolon in a literal */
%let list = %str(a, b; c);
%put &list;               /* prints: a, b; c */

/* CORRECT - mask & in a literal so it does not resolve */
%let template = %nrstr(link=&id);
%put &template;           /* prints: link=&id — does not resolve &id */

/* CORRECT - execution-time mask of unbalanced quote from user input */
%let msg = %bquote(it's a test);
%put &msg;                /* handles the lone apostrophe */

/* CORRECT - strongest: pass variable NAME, not &var */
%let raw = %superq(user_input);
```

```sas
/* WRONG - %str around a &var still resolves it */
%let x = %str(&somevar);   /* &somevar resolves BEFORE %str sees it */
/* need %nrstr for literal, or %superq for resolve-once-safely */
```

### Rule: Quote type does NOT suppress `&` resolution in macro-context statements

In DATA/PROC step string literals, single quotes keep `&var` literal while
double quotes resolve it. In macro-context statements (`%put`, `%let`,
`%if`), the macro processor scans for `&` and `%` triggers *before* the
statement receives its argument, so quote type does not suppress
resolution. `%put 'table: &name';` still resolves `&name` — the single
quotes become literal output characters. Use `%nrstr(...)` or
`%str(%&...)` to mask triggers in macro context.

```sas
/* CORRECT - %nrstr masks & in a macro-context statement */
%put %nrstr(table: &name);    /* prints: table: &name */

/* CORRECT - DATA-step literal: single quotes DO keep &name literal */
data _null_;
  x = 'table: &name';           /* x = "table: &name" literally */
  y = "table: &name";           /* y = "table: <resolved>" */
run;
```

```sas
/* WRONG - single quotes inside %put do NOT stop resolution */
%put 'table: &name';          /* still resolves &name; quotes become literal */
```

### Rule: `call symputx` takes a scope argument — use it

`call symputx('var', value)` defaults to writing in the most-local
non-empty scope, which can surprise inside nested macros. Pass `'G'`
(global), `'L'` (local to current macro), or `'F'` (most-local
non-empty — the default made explicit) so the reader can see intent.

```sas
/* CORRECT - scope is explicit */
data _null_;
  set counts(obs=1);
  call symputx('n_rows', n, 'L');   /* local to current macro */
run;
```

```sas
/* WRONG - defaults to 'F'; in a nested context may silently hit the wrong scope */
data _null_;
  set counts(obs=1);
  call symputx('n_rows', n);
run;
```

## Function / Statement Quick Ref

| Name | Syntax | Purpose | Common mistake |
|------|--------|---------|----------------|
| `%str` | `%str(text with , ; = etc.)` | Mask special chars at compile time | Using `%str(&var)` expecting `&var` to NOT resolve (still does) |
| `%nrstr` | `%nrstr(&var literal)` | Mask `&` and `%` triggers at compile time | Omitting when passing a literal with `&var` through a parameter |
| `%bquote` | `%bquote(&var with unbalanced quote)` | Mask special chars at macro-execution time | Using `%str` when unbalanced quotes require `%bquote` |
| `%nrbquote` | `%nrbquote(&var with & or %)` | Mask `&`, `%`, and special chars at execution time | Picking wrong quote-function tier |
| `%superq` | `%superq(varname)` — no `&` | Return unresolved value of a macro var; strongest mask | Writing `%superq(&var)` — pass the NAME, not `&var` |
| `call symputx` | `call symputx('var', value, 'G'|'L'|'F');` | Write a macro variable from a DATA step | Omitting scope arg — defaults to most-local; surprises in nested contexts |
| `symget` | `symget('var')` | Read a macro variable inside a DATA step | Using `symget` when compile-time `&var` would work |

## Silent Pitfalls

- **`%let x = &y;` inside a macro without `%local x;`** — writes `x` to
  the most-local existing scope; if `x` exists at an outer level, the
  outer `x` is overwritten. See "%local discipline" rule above.

- **`'&var'` quote-suppression myth in macro context** — in macro
  statements (`%put`, `%let`, `%if`) the macro processor scans `&` and
  `%` triggers before the statement receives its argument, so quote
  type does not suppress resolution. Use `%nrstr(...)` or
  `%str(%&...)` to mask.

- **`%str(&var)` vs `%nrstr(&var)`** — `%str` masks commas / semicolons
  / equals / etc., but NOT `&` or `%`. Only the `nr` variants mask the
  triggers themselves.

- **`call symputx` without scope arg in a nested macro** — default is
  most-local-non-empty, which may be an inner scope and vanish on
  `%mend`. Pass `'L'` or `'G'` explicitly.

## Anti-patterns (STOP signs)

- `%let x = &y;` inside a `%macro` with no `%local x;` → scope leak.
- `%put 'text with &var';` expecting `&var` to stay literal → use
  `%nrstr(...)`.
- `%str(&var)` expecting the `&` to be masked → use `%nrstr` or
  `%superq`.
- `call symputx('x', value);` inside nested macros with no scope arg →
  pass `'L'` or `'G'`.
- `%superq(&var)` — `%superq` takes the variable name, not `&var`.
