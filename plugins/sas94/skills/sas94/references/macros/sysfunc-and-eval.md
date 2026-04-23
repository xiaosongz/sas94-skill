---
title: '%sysfunc, %eval, %sysevalf — calling functions and doing arithmetic in macro code'
loaded_when: 'calling a DATA-step function from macro context (`%sysfunc`); integer arithmetic (`%eval`) or floating-point arithmetic (`%sysevalf`) in macro expressions; conversion types `integer` / `ceil` / `floor` / `boolean`.'
---

## Critical Rules

### Rule: `%sysfunc` gives macro code access to DATA-step functions — pass the optional format when needed

`%sysfunc(func(args))` calls a DATA-step function from macro context.
The optional second argument is a format specification that controls
how the returned value is rendered back into the macro text stream
(for example `%sysfunc(today(), yymmdd10.)`).

```sas
/* CORRECT - formatted output */
%let today_iso = %sysfunc(today(), yymmdd10.);      /* 2026-04-23 */

/* CORRECT - existence check inline */
%if %sysfunc(exist(&libds)) %then %do;
  /* ... */
%end;
```

```sas
/* WRONG - missing format on a date function; returns raw SAS date integer */
%let today_iso = %sysfunc(today());    /* 24219 — probably not what you wanted */
```

### Rule: `%eval` is integer-only; use `%sysevalf` for floating arithmetic

`%eval(&a + &b)` evaluates integer arithmetic and relational expressions.
Anything with a decimal point silently truncates or fails. For floating
arithmetic, use `%sysevalf(&a / &b, <conversion>)` and supply the
conversion type:

- `integer` — truncate toward zero.
- `ceil` — round toward +infinity.
- `floor` — round toward -infinity.
- `boolean` — 0 if result is 0, else 1.

Omitting the conversion returns a floating-point representation that
may include a decimal; most call sites want `integer` / `ceil` /
`floor` / `boolean`.

```sas
/* CORRECT - integer arithmetic with %eval */
%let n = %eval(10 + 5);                 /* 15 */
%let flag = %eval(&x > 0 and &y ne .);  /* 0 or 1 */

/* CORRECT - floating with explicit conversion */
%let pages = %sysevalf(&n_rows / &page_size, ceil);   /* number of pages */
%let ratio = %sysevalf(&num / &den);                  /* raw float, e.g. 0.3333333 */
%let have  = %sysevalf(&x, boolean);                  /* 0 if x empty/0, else 1 */
```

```sas
/* WRONG - decimal in %eval silently breaks */
%let pages = %eval(&n_rows / &page_size);    /* integer division — truncates! */
%let r     = %eval(0.5 + 0.5);               /* ERROR: character operand */

/* WRONG - %sysevalf with no conversion when caller wants an integer */
%let pages = %sysevalf(&n_rows / &page_size);  /* returns 12.5 not 13 */
```

## Canonical Idioms

### Idiom: Guarded-execution `iftrue=` parameter (uses `%eval` + `%unquote`)

Allow the caller to suppress the macro's side effects with a one-line
predicate, without wrapping every call site in an outer `%if`. The
macro evaluates `iftrue` as a macro expression and `%return`s early
when false. `%unquote` strips any `%str(...)` quoting so `%eval` sees
the raw expression; this is why `iftrue=` defaults look like
`iftrue=%str(1=1)`.

```sas
%macro mp_hashdataset(libds, outds=work._data_, iftrue=%str(1=1)
)/*/STORE SOURCE*/;
  %local ...;
  %if not(%eval(%unquote(&iftrue))) %then %return;
  /* real work */
%mend mp_hashdataset;
```

## Function / Statement Quick Ref

| Name | Syntax | Purpose | Common mistake |
|------|--------|---------|----------------|
| `%sysfunc` | `%sysfunc(func(args), format)` | Call a DATA-step function from macro code | Forgetting the optional format argument |
| `%eval` | `%eval(&a + &b)` | Integer-only arithmetic and relationals in macro | Using on decimals — use `%sysevalf` |
| `%sysevalf` | `%sysevalf(&a / &b, ceil)` | Floating-point arithmetic in macro | Omitting conversion type (`integer`, `ceil`, `floor`, `boolean`) |
| `%do` / `%end` | `%do i = 1 %to 10; ... %end;` | Iterative macro loop | Using `&i` after `%end;` — value is last-iter value |
| `%if` / `%then` / `%else` | `%if cond %then %do; ... %end; %else %do; ... %end;` | Conditional macro logic | Using DATA-step `if` vs macro `%if` |
| `%put` | `%put NOTE- message;` | Write to the SAS log | Using `%put` without `NOTE-` / `WARNING-` / `ERROR-` tag |

## Silent Pitfalls

- **`%eval` on a decimal expression** — character-operand error or
  silent truncation depending on the form. Any arithmetic that can
  produce a non-integer must use `%sysevalf`.

- **`%sysevalf` without a conversion type** — returns the float as-is
  (e.g. `12.5`), which then gets embedded into generated SAS code.
  Almost every call site wants `integer` / `ceil` / `floor` / `boolean`.

- **`%sysfunc` of a function that expects a formatted value without
  passing the format** — e.g. `%sysfunc(today())` returns an integer
  date, not an ISO string. Pass `yymmdd10.`, `date9.`, etc.

- **`%sysfunc(putn(&num, dollar12.))` vs `%sysfunc(put(&num,
  dollar12.))`** — `PUT` is a compile-time function not available via
  `%sysfunc`; use `PUTN` / `PUTC` (runtime) variants inside `%sysfunc`.

## Anti-patterns (STOP signs)

- `%eval(&a / &b)` where either operand is a decimal or the quotient
  can be fractional → use `%sysevalf(..., integer|ceil|floor)`.
- `%sysevalf(&n_rows / &page_size)` with no conversion type, then
  embedding the result in `do i=1 to &pages;` → will emit
  `do i=1 to 12.5;` and blow up. Add `, ceil`.
- `%sysfunc(today())` or `%sysfunc(datetime())` with no format → raw
  numeric integer lands in generated code.
- `%sysfunc(put(&x, 8.))` → use `putn` / `putc` inside `%sysfunc`.
