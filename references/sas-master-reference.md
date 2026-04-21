---
title: SAS 9.4 master reference
scope: Grammar overview, execution model, PDV semantics, and top-N pitfalls that span multiple SAS topics.
loaded_when: New `.sas` file, study program skeleton, cross-cutting grammar or scope questions.
last_reviewed: 2026-04-21
reviewer: xiaosongz
---

## Overview

SAS 9.4 has two compile-time languages that share a file — the macro
processor (which generates SAS code) and the base SAS step languages
(DATA step, PROC). Most "bug" reports are actually language-boundary
errors: a macro that resolves at the wrong time, a DATA step that
forgets `retain`, or a PROC SQL join that silently duplicates rows. This
file is the top-level router: load it at the start of any new `.sas`
file, then follow the `See Also` pointers to topic-specific reference
files. The top-20 rules below are aggregated and de-duplicated from
`references/macros.md`, `references/data-step.md`, and the 5
hand-transcribed pitfalls in
`pipeline/manual/gwu-data-mining-5-items.md`.

## Critical Rules

### Rule 1: Every `%macro` signature must carry parentheses `()`

Source: https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/file/hasMacroParentheses.ts

Positional parameters and `/STORE SOURCE`, `/des=`, `/SECURE` options all
require the `()` form; without it `sasjs/lint hasMacroParentheses` fires
and many call-site bugs become silent.

```sas
/* CORRECT */
%macro somemacro();
  %put &sysmacroname;
%mend somemacro;
```

```sas
/* WRONG */
%macro somemacro;
  %put &sysmacroname;
%mend somemacro;
```

### Rule 2: Close every `%mend` with its macro name

Source: https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/file/hasMacroNameInMend.ts

Ambiguous `%mend;` breaks code navigation and silently masks missing
`%mend` for the outer macro when two macros sit side-by-side.

```sas
/* CORRECT */
%macro somemacro;
  %put &sysmacroname;
%mend somemacro;
```

```sas
/* WRONG */
%macro somemacro;
  %put &sysmacroname;
%mend;
```

### Rule 3: Never nest `%macro` definitions

Source: https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/file/noNestedMacros.ts

Nested `%macro` recompiles on every outer call; `sasjs/lint
noNestedMacros` flags it. Define helpers at top level and call them.

```sas
/* CORRECT */
%macro inner();
  %put inner;
%mend inner;
%macro outer();
  %inner()
%mend outer;
```

```sas
/* WRONG */
%macro outer();
  %macro inner();
    %put inner;
  %mend inner;
%mend outer;
```

### Rule 4: Use strict macro-definition syntax — no whitespace in parameter names, no unknown options

Source: https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/file/strictMacroDefinition.ts

`sasjs/lint strictMacroDefinition` rejects `var 1` style params and
unknown options after `/`.

```sas
/* CORRECT */
%macro somemacro(var1, var2) /minoperator;
```

```sas
/* WRONG */
%macro somemacro(var 1, var2) /minXoperator;
```

### Rule 5: Every `.sas` file begins with a Doxygen header

Source: https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/file/hasDoxygenHeader.ts

`@file`, `@brief`, `@param [in]`, `@version`, `@author` — consistent
across `sasjs/core` and enforced by `sasjs/lint hasDoxygenHeader`.

```sas
/* CORRECT */
/**
  @file
  @brief One-line purpose
  @param [in] libds library.dataset
  @version 9.2
  @author <name>
**/
%macro mf_getuniquelibref(prefix=mclib);
%mend mf_getuniquelibref;
```

```sas
/* WRONG - no header */
%macro mf_getuniquelibref(prefix=mclib);
%mend mf_getuniquelibref;
```

### Rule 6: Security-sensitive or shared macros carry required options (`SECURE`, `STORE SOURCE`)

Source: https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/file/hasRequiredMacroOptions.ts

`sasjs/lint hasRequiredMacroOptions` enforces a project-configured option
list. Whitespace-sensitive: `SE CURE` is not `SECURE`.

```sas
/* CORRECT */
%macro somemacro / SECURE;
%macro another  / SECURE SRC;
```

```sas
/* WRONG */
%macro somemacro(var1, var2) / SE CURE;
```

### Rule 7: Indent by a consistent multiple of spaces (default 2)

Source: https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/line/indentationMultiple.ts

Non-multiple indentation confuses nested `%do` / `do` / `%if` structure.

```sas
/* CORRECT */
data out;
  set in;
  if x > 0 then y = log(x);
run;
```

```sas
/* WRONG */
data out;
 set in;
   if x > 0 then y = log(x);
run;
```

### Rule 8: Keep lines under the configured maximum length (default 300)

Source: https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/line/maxLineLength.ts

Long inline `where` clauses hide logic behind horizontal scroll. Break
after commas or logical operators.

```sas
/* CORRECT */
where service_dt between '01JAN2023'd and '31DEC2023'd
  and paid_amt > 0
  and not missing(member_id);
```

```sas
/* WRONG - 300+ char inline */
where service_dt between '01JAN2023'd and '31DEC2023'd and paid_amt > 0 and not missing(member_id) and provider_npi ne '' and diagnosis_code in ('E11.9','I10','N18.3','J44.9');
```

### Rule 9: Indent with spaces, never tab characters

Source: https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/line/noTabs.ts

`sasjs/lint noTabs` rejects any `\t`; tabs render inconsistently across
editors.

```sas
/* CORRECT */
data out;
  set in;
run;
```

```sas
/* WRONG - leading tab */
data out;
	set in;
run;
```

### Rule 10: Strip trailing whitespace from every line

Source: https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/line/noTrailingSpaces.ts

Trailing whitespace breaks `diff --word-diff` and causes spurious merge
conflicts.

```sas
/* CORRECT */
data out; set in; run;
```

```sas
/* WRONG - trailing space after semicolon */
data out; set in; run;··
```

### Rule 11: No "gremlin" non-printable characters in source

Source: https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/line/noGremlins.ts

Invisible characters in a `where` clause or string literal break equality
compares at runtime with no log diagnostic.

```sas
/* CORRECT - plain ASCII */
where member_id = 'A12345';
```

```sas
/* WRONG - zero-width no-break space inside literal */
where member_id = 'A12345';  /* contains invisible U+FEFF */
```

### Rule 12: Never commit encoded-password literals (`{SAS001}`, `{SAS002}`, `{SASENC}`)

Source: https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/line/noEncodedPasswords.ts

SAS encoded passwords are trivially reversible. Read secrets from env or
autoexec, never embed in source.

```sas
/* CORRECT */
libname db oracle user=svc password="&env_db_pw" path=prod;
```

```sas
/* WRONG */
libname db oracle user=svc password="{SAS002}D41D8CD98F00B204E9800998ECF8427E" path=prod;
```

### Rule 13: Configure consistent line endings (`lineEndings`)

Source: https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/file/lineEndings.ts

`sasjs/lint lineEndings` enforces a single convention (LF or CRLF).
Mixed endings within one file break some SAS-server line counters and
every diff tool.

```sas
/* CORRECT - single LF ending */
%put 'hello';\n%put 'world';\n
```

```sas
/* WRONG - mixed CRLF + LF */
%put 'hello';\r\n%put 'test';\n%put 'world';\r\n
```

### Rule 14: LAG is queue-based — call unconditionally, gate usage afterwards (GWU §1)

Source: https://github.com/jphall663/GWU_data_mining — hand-transcribed in `pipeline/manual/gwu-data-mining-5-items.md`.

`LAG(x)` advances a queue only when called. Inside a conditional, the
queue advances only on matched rows, misaligning the lag.

```sas
/* CORRECT */
data out;
  set in;
  prev_x = lag(x);
  if month = 1 then lag_x = prev_x;
run;
```

```sas
/* WRONG */
data out;
  set in;
  if month = 1 then lag_x = lag(x);
run;
```

### Rule 15: MERGE silently overwrites same-named variables (GWU §2)

Source: https://github.com/jphall663/GWU_data_mining — hand-transcribed in `pipeline/manual/gwu-data-mining-5-items.md`.

When two MERGE sides share a column name, the right-hand side's value
wins with no log diagnostic. Rename on input, then coalesce.

```sas
/* CORRECT */
data both;
  merge a(rename=(amount=amount_a))
        b(rename=(amount=amount_b));
  by id;
  amount = coalesce(amount_a, amount_b);
run;
```

```sas
/* WRONG */
data both;
  merge a b;
  by id;
run;
```

### Rule 16: PROC APPEND uses BASE's schema — new columns dropped without FORCE (GWU §3)

Source: https://github.com/jphall663/GWU_data_mining — hand-transcribed in `pipeline/manual/gwu-data-mining-5-items.md`.

`PROC APPEND` uses `BASE` as the column contract. Columns present in
`DATA` but not `BASE` vanish silently unless `FORCE` is specified.

```sas
/* CORRECT */
data a;
  set a;
  length new_col $32;
run;
proc append base=a data=b; run;
```

```sas
/* WRONG */
proc append base=a data=b; run;  /* b.new_col silently dropped */
```

### Rule 17: SQL join vs MERGE — different semantics, different failure modes (GWU §4)

Source: https://github.com/jphall663/GWU_data_mining — hand-transcribed in `pipeline/manual/gwu-data-mining-5-items.md`.

MERGE requires sorted BY and right-overwrites silently; SQL joins do not
require sorting and require explicit `COALESCE` for same-named columns.

```sas
/* CORRECT */
proc sql;
  create table t as
  select a.id, coalesce(a.amount, b.amount) as amount
  from a full join b on a.id = b.id;
quit;
```

```sas
/* WRONG */
proc sql;
  create table t as
  select a.*, b.*
  from a inner join b on a.id = b.id;
quit;
```

### Rule 18: Macro-quote single vs double — `'&var'` is literal, `"&var"` resolves (GWU §5)

Source: https://github.com/jphall663/GWU_data_mining — hand-transcribed in `pipeline/manual/gwu-data-mining-5-items.md`.

Single quotes suppress macro resolution; double quotes resolve. `%str`
does NOT override this. Use `%nrstr` when you want `&` and `%` to stay
literal.

```sas
/* CORRECT */
%let name = claims;
%put "table: &name";                 /* prints: table: claims */
%put %nrstr(literal &name unresolved);
```

```sas
/* WRONG */
%let name = claims;
%put 'table: &name';                 /* prints: table: &name */
```

### Rule 19: Declare `%local` for every non-parameter symbol inside a macro

Source: https://github.com/sasjs/core/blob/3a54b9c796c0bfe477d1aefc1e22b9ff9f2c96c2/base/mp_hashdataset.sas

Without `%local`, `%let x = ...;` inside a macro writes to the
most-local *existing* scope, which is often the global scope. The
`sasjs/core` base macros declare every helper symbol `%local` at the top
of the body.

```sas
/* CORRECT */
%macro mp_hashdataset(libds, outds=work._data_);
  %local keyvar prevkeyvar lastvar cvars nvars;
  %let keyvar = %mf_getuniquename();
  /* body */
%mend mp_hashdataset;
```

```sas
/* WRONG - keyvar leaks to global scope */
%macro mp_hashdataset(libds, outds=work._data_);
  %let keyvar = %mf_getuniquename();
%mend mp_hashdataset;
```

### Rule 20: Structure every macro signature as positional-required + keyword-optional, and close with `/*/STORE SOURCE*/`

Source: https://github.com/sasjs/core/blob/3a54b9c796c0bfe477d1aefc1e22b9ff9f2c96c2/base/mf_existds.sas

Required inputs are positional (stable order, stable call site); optional
behavior is keyword-with-default. The closing `)/*/STORE SOURCE*/;` on
one line is the `sasjs/core` signature convention.

```sas
/* CORRECT */
%macro mf_existds(libds
)/*/STORE SOURCE*/;
  %if %sysfunc(exist(&libds)) ne 1 & %sysfunc(exist(&libds,VIEW)) ne 1
    %then 0;
  %else 1;
%mend mf_existds;
```

```sas
/* WRONG - all keyword with no required positional */
%macro mf_existds(libds=);
%mend mf_existds;
```
## Reference-file Pointers

Load the topic-specific reference when the task matches its scope.

- [macros.md](macros.md) — `%let`, `%macro` scope, quoting (`%str`,
  `%nrstr`, `%bquote`, `%superq`), `&&var` resolution, `call symput` /
  `symget`. Seeded in v0.0.1.
- [data-step.md](data-step.md) — MERGE / BY, `first.` / `last.`,
  `retain`, arrays, PDV initialization. Seeded in v0.0.1.
- [proc-sql.md](proc-sql.md) — joins, dedup, `INTO :macvar` list
  targets, `RESET`. **Stub — populated in v0.0.2+.**
- [base-procs.md](base-procs.md) — FREQ, MEANS, UNIVARIATE, SORT,
  TRANSPOSE, REPORT. **Stub — populated in v0.0.2+.**
- [stat-procs.md](stat-procs.md) — LOGISTIC, GLM, MIXED, GENMOD,
  SURVEY\*, LIFETEST. **Stub — populated in v0.0.2+.**
- [hash-tables.md](hash-tables.md) — `declare hash`, `definekey`,
  `hashiter`. **Stub — populated in v0.0.2+.**
- [ods-and-output.md](ods-and-output.md) — ODS RTF / EXCEL / PDF, `ODS
  OUTPUT`, ODS GRAPHICS, GTL. **Stub — populated in v0.0.2+.**
- [formats-informats.md](formats-informats.md) — PROC FORMAT, date/time
  formats, `input()` / `put()`. **Stub — populated in v0.0.2+.**
- [functions-reference.md](functions-reference.md) — function-signature
  cheatsheet by category. **Stub — populated in v0.0.2+.**
- [idioms-from-lexjansen.md](idioms-from-lexjansen.md) — real-world
  idioms distilled from SUGI and SAS Global Forum papers. **Stub —
  populated in v0.0.2+.**

## Function / Statement Quick Ref

| Name | Syntax | Purpose | Common mistake | Doc URL |
|------|--------|---------|----------------|---------|
| `%macro` / `%mend` | `%macro name(args); ... %mend name;` | Macro definition | Missing `()`, bare `%mend;` | TODO (source pending) |
| `%let` | `%let var = value;` | Macro variable assignment | Scope leak without `%local` | TODO (source pending) |
| `%local` / `%global` | `%local v1 v2;` | Macro-symbol scope declaration | Declaring after first `%let` — too late | TODO (source pending) |
| `data` / `set` / `run` | `data out; set in; run;` | Minimum DATA step | Forgetting `run;` (interactive sessions) | TODO (source pending) |
| `merge` / `by` | `data c; merge a b; by id; run;` | BY-group DATA-step join | Unsorted inputs, silent overwrite | TODO (source pending) |
| `retain` | `retain var initial;` | Carry PDV value across iterations | Forgetting → accumulator resets to missing | TODO (source pending) |
| `proc sql` | `proc sql; <select>; quit;` | SQL block | Missing `quit;` | TODO (source pending) |
| `libname` | `libname ref engine "path";` | Attach a library | Forgetting to `libname ref clear;` after use | TODO (source pending) |

## Silent Pitfalls

See topic-specific reference files for full lists:
- Macro scope and resolution pitfalls — `references/macros.md`.
- MERGE / LAG / PROC APPEND / SQL-join pitfalls —
  `references/data-step.md` and
  `pipeline/manual/gwu-data-mining-5-items.md`.

## Anti-patterns (STOP signs)

**STOP** and re-check whenever you see any of these. Each is sourced from
the 20 rules above:

- `%macro foo; ... %mend;` (missing `()`) → Rule 1.
- `%mend;` without the macro name → Rule 2.
- `%macro outer; %macro inner; ... %mend; %mend;` (nested) → Rule 3.
- Doxygen-less `.sas` file → Rule 5.
- Tab-indented, trailing-space, or gremlin-laden lines → Rules 9–11.
- Encoded password `{SAS00X}` in source → Rule 12.
- `if cond then lagx = lag(x);` → Rule 14.
- `merge a b; by id; run;` without handling same-named columns → Rule 15.
- `proc append base=a data=b;` with mismatched schema → Rule 16.
- `select a.*, b.*` across a shared-column join → Rule 17.
- `'&var'` when you wanted resolution → Rule 18.
- `%let x = ...;` inside a macro with no `%local x;` → Rule 19.

## See Also

- [macros.md](macros.md) — deep dive on Rules 1–6, 18, 19, 20.
- [data-step.md](data-step.md) — deep dive on Rules 7–11, 14–17.
- `pipeline/manual/gwu-data-mining-5-items.md` — source of Rules 14–18.
- `docs/design.md` — skill architecture and versioning semantics.
