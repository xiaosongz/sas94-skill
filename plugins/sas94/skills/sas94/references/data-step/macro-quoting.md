---
title: DATA-step quotes and macro-context quote masking
loaded_when: '"macro quoting", "%nrstr", "%str", single vs double quotes, "&var" in a string literal, "%put" not printing what was expected, "compile-time" vs "execute-time" macro resolution.'
---

## Critical Rules

### Rule 5: Macro resolution and quote semantics — DATA-step single-vs-double quotes, macro-context masks via `%nrstr` (GWU §5)

In DATA / PROC step string literals, single quotes keep `&var` literal
while double quotes resolve it. In macro-context statements (`%put`,
`%let`, `%if`), the macro processor scans for `&` and `%` triggers
*before* the statement receives its argument, so the quote type does not
suppress resolution — mask triggers with `%nrstr(...)` or `%str(%&...)`.

```sas
/* CORRECT — single-quoted DATA-step literal: &svc is not resolved */
%let svc = claims;
data _null_;
  lbl = 'source: &svc';
  put lbl;          /* writes: source: &svc */
run;

/* CORRECT — double-quoted DATA-step literal: &svc resolves */
data _null_;
  lbl = "source: &svc";
  put lbl;          /* writes: source: claims */
run;

/* CORRECT — macro-context masking requires %nrstr, not quotes */
%put %nrstr(literal &svc is unresolved);   /* writes: literal &svc is unresolved */
```

```sas
/* WRONG — single quotes in %put do NOT suppress resolution */
%let svc = claims;
%put 'source: &svc';   /* writes: source: claims — quotes are literal output chars */
```

## Silent Pitfalls

- **Macro-context quote masking** — single-quoted `%put '&var'` still
  resolves `&var` because the macro processor tokenizes before the
  statement receives its argument. Use `%nrstr(...)` to mask triggers.
- **DATA-step single-quote habit carried into macro code** — the two
  contexts have opposite rules for single quotes. Know which parser
  owns the current statement before choosing a quote style.
- **`call symputx` scope default** — `call symputx('v', x)` writes to
  the *most local* enclosing macro scope. In open code this is
  surprising; pass `'G'` for global or `'L'` for the local `%macro`
  scope explicitly.

## Anti-patterns (STOP signs)

**STOP** when you see any of the following — the code compiles and
produces output, but the output is almost certainly wrong:

- `%put '&var';` expecting single quotes to suppress macro resolution →
  see Rule 5 / GWU §5.
- Using `symget('v')` inside a DATA step when compile-time `&v` would
  work — `symget` runs at *execute* time and is 10-100x slower per row.

## Related

Macro-side detail (scope, `%nrstr` vs `%str` vs `%superq`, nested
resolution): `../macros/scope-and-quoting.md`. DATA-step side of
`symputx` / `symget`: see `retain-pdv.md` for the PDV model these
routines plug into.
