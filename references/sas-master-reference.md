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

## Critical Rules (Top-20 Aggregated)

This file is the cross-topic aggregator — the ≤8-rule cap that applies
to topic reference files (see `docs/CONTRIBUTING.md`) is intentionally
waived here. The 20 rules below are de-duplicated across
`references/macros.md`, `references/data-step.md`, and
`pipeline/manual/gwu-data-mining-5-items.md`; each rule points back to
the topic file where its full treatment lives.

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
%macro somemacro();
  %put &sysmacroname;
%mend somemacro;
```

```sas
/* WRONG */
%macro somemacro();
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
/* WRONG - sasjs/lint strictMacroDefinition rejects; SAS itself compiles silently */
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
/* WRONG - sasjs/lint hasDoxygenHeader rejects; SAS itself compiles silently */
%macro mf_getuniquelibref(prefix=mclib);
%mend mf_getuniquelibref;
```

### Rule 6: Security-sensitive or shared macros carry required options (`SECURE`, `STORE SOURCE`)

Source: https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/file/hasRequiredMacroOptions.ts

`sasjs/lint hasRequiredMacroOptions` enforces a project-configured option
list. Whitespace-sensitive: `SE CURE` is not `SECURE`.

```sas
/* CORRECT */
%macro somemacro() / SECURE;
%macro another()  / SECURE SRC;
```

```sas
/* WRONG - sasjs/lint hasRequiredMacroOptions rejects (whitespace splits SECURE); SAS compiles but treats "SE" and "CURE" as separate tokens */
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
/* WRONG - trailing whitespace on code lines (invisible, but present)

   After the semicolon on each code line below, the source file carries
   trailing ASCII space characters (0x20). `sasjs/lint noTrailingSpaces`
   auto-fixes these. Git history diffs flood with whitespace-only churn
   when left in.
*/
%put 'hello';
%put 'world';
/* imagine two or more 0x20 bytes after each semicolon, before the newline */
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
/* WRONG - gremlin bytes inside the quoted string (invisible in most editors)

   The literal bytes between 'A' and '12345' below include U+FEFF (BOM,
   three bytes: EF BB BF) copied from an Excel export. `sasjs/lint noGremlins`
   flags the token; the WHERE clause silently fails to match cleanly-typed
   'A12345' rows.
*/
where member_id = 'A<U+FEFF>12345';   /* actual file would have invisible bytes */
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

### Rule 13: Use Unix LF (\n) line endings, never CRLF

Source: https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/file/lineEndings.ts

Why: `sasjs/lint lineEndings` enforces the configured terminator. Most SAS
Unix/Linux hosts choke on Windows CRLF in macros that splice strings byte
by byte; mixed endings in a single file produce inconsistent diffs and
break downstream tools that rely on line counts.

Verification (shell):

```bash
# CORRECT — pure LF
hexdump -C foo.sas | grep '0a$' | head -1      # trailing bytes: ... 3b 0a

# WRONG — CRLF remnants
hexdump -C foo.sas | grep '0d 0a' | head -1   # found CR (0d) before LF (0a)
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

### Rule 16: PROC APPEND variable-shape rules (GWU §3)

Source: https://github.com/jphall663/GWU_data_mining — hand-transcribed in `pipeline/manual/gwu-data-mining-5-items.md`.

`PROC APPEND BASE=a DATA=b` uses BASE's variable definitions. Without
`FORCE`, any variable in DATA= that is absent from BASE= causes the step
to **fail with ERROR** — nothing is appended. With `FORCE`, the extra
variable is **dropped with a WARNING** and the step proceeds. The silent
failure mode is different: when BASE= carries a variable absent from
DATA=, appended rows get missing values in that column, no diagnostic —
easy to miss when BASE= has been recently extended.

```sas
/* CORRECT — align DATA columns to BASE before appending, or use FORCE knowingly */
proc append base=claims data=claims_new force;   /* drops new-in-DATA vars w/ WARNING */
run;

/* or: explicitly reshape DATA to match BASE */
data claims_aligned;
  set claims_new;
  keep patient_id claim_dt cost;   /* whatever BASE=claims has */
run;
proc append base=claims data=claims_aligned;    /* no FORCE needed */
run;
```

```sas
/* WRONG — DATA has a column absent from BASE; step errors without FORCE */
proc append base=claims data=claims_new;
run;
/* ERROR: Variable new_flag in DATA set not in BASE set. No appending done. */

/* Subtler silent mode: BASE has a column absent from DATA */
proc append base=claims_v2 data=claims_v1;   /* v2 added new_flag; v1 lacks it */
run;
/* Step succeeds; new_flag is missing for every v1 row — no WARNING. */
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

### Rule 18: Macro resolution and quote semantics (GWU §5)

Source: https://github.com/jphall663/GWU_data_mining — hand-transcribed in `pipeline/manual/gwu-data-mining-5-items.md`.

In DATA/PROC step string literals, single quotes keep `&var` literal while
double quotes resolve it. In macro-context statements (`%put`, `%let`,
`%if`), the macro processor scans for `&` and `%` triggers *before* the
statement receives its argument, so quote type does not suppress
resolution — use `%nrstr(...)` or `%str(%&...)` to mask triggers.

```sas
/* CORRECT — single-quoted DATA-step literal: &name is not resolved */
%let name = claims;
data _null_;
  x = 'table: &name';
  put x;          /* writes: table: &name */
run;

/* CORRECT — double-quoted DATA-step literal: &name resolves */
data _null_;
  x = "table: &name";
  put x;          /* writes: table: claims */
run;

/* CORRECT — macro-context masking requires %nrstr, not quotes */
%put %nrstr(literal &name is unresolved);     /* writes: literal &name is unresolved */
```

```sas
/* WRONG — single quotes in %put do NOT suppress resolution */
%let name = claims;
%put 'table: &name';   /* writes: table: claims — quotes are literal output chars */
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
  `symget`.
- [data-step.md](data-step.md) — MERGE / BY, `first.` / `last.`,
  `retain`, arrays, PDV initialization.
- [proc-sql.md](proc-sql.md) — joins, dedup, `INTO :macvar` list
  targets, `RESET`.
- [base-procs.md](base-procs.md) — FREQ, MEANS, UNIVARIATE, SORT,
  TRANSPOSE, REPORT.
- [stat-procs.md](stat-procs.md) — LOGISTIC, GLM, MIXED, GENMOD,
  SURVEY\*, LIFETEST.
- [hash-tables.md](hash-tables.md) — `declare hash`, `definekey`,
  `hashiter`.
- [ods-and-output.md](ods-and-output.md) — ODS RTF / EXCEL / PDF, `ODS
  OUTPUT`, ODS GRAPHICS, GTL.
- [formats-informats.md](formats-informats.md) — PROC FORMAT, date/time
  formats, `input()` / `put()`.
- [functions-reference.md](functions-reference.md) — function-signature
  cheatsheet by category.
- [idioms-from-lexjansen.md](idioms-from-lexjansen.md) — real-world
  idioms distilled from SUGI and SAS Global Forum papers.

## Function / Statement Quick Ref

| Name | Syntax | Purpose | Common mistake | Doc URL |
|------|--------|---------|----------------|---------|
| `%macro` / `%mend` | `%macro name(args); ... %mend name;` | Macro definition | Missing `()`, bare `%mend;` | [`%macro` / `%mend`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=mcrolref&docsetTarget=titlepage.htm) |
| `%let` | `%let var = value;` | Macro variable assignment | Scope leak without `%local` | [`%let`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=mcrolref&docsetTarget=titlepage.htm) |
| `%local` / `%global` | `%local v1 v2;` | Macro-symbol scope declaration | Declaring after first `%let` — too late | [`%local` / `%global`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=mcrolref&docsetTarget=titlepage.htm) |
| `data` / `set` / `run` | `data out; set in; run;` | Minimum DATA step | Forgetting `run;` (interactive sessions) | [`DATA Statement`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lestmtsref&docsetTarget=titlepage.htm) |
| `merge` / `by` | `data c; merge a b; by id; run;` | BY-group DATA-step join | Unsorted inputs, silent overwrite | [`MERGE Statement`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lestmtsref&docsetTarget=titlepage.htm) |
| `retain` | `retain var initial;` | Carry PDV value across iterations | Forgetting → accumulator resets to missing | [`RETAIN Statement`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lestmtsref&docsetTarget=titlepage.htm) |
| `proc sql` | `proc sql; <select>; quit;` | SQL block | Missing `quit;` | [`PROC SQL`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=proc&docsetTarget=titlepage.htm) |
| `libname` | `libname ref engine "path";` | Attach a library | Forgetting to `libname ref clear;` after use | [`LIBNAME Statement`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lestmtsref&docsetTarget=titlepage.htm) |

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
- `proc append base=a data=b;` where DATA has a column not in BASE, no
  `FORCE` → ERROR, step fails → Rule 16.
- `select a.*, b.*` across a shared-column join → Rule 17.
- `%put 'text with &var';` expecting quotes to suppress resolution → Rule 18.
- `%let x = ...;` inside a macro with no `%local x;` → Rule 19.

## See Also

- [macros.md](macros.md) — deep dive on Rules 1–6, 18, 19, 20.
- [data-step.md](data-step.md) — deep dive on Rules 7–11, 14–17.
- `pipeline/manual/gwu-data-mining-5-items.md` — source of Rules 14–18.
- `docs/design.md` — skill architecture and versioning semantics.
