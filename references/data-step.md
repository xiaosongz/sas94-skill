---
title: DATA step reference
scope: DATA-step iteration semantics — MERGE / BY processing, `first.`/`last.`, `retain` / PDV carry-forward, arrays, LAG queue behavior, PROC APPEND shape rules, SQL-vs-MERGE distinction, and DATA-step quote / macro resolution. File hygiene (indentation, line length, tabs, trailing whitespace, gremlins, encoded passwords) from `sasjs/lint` appears in a trailing section.
loaded_when: '"MERGE", "BY processing", "first.", "last.", "retain", "array", "PDV", "LAG", "PROC APPEND", or any DATA-step authoring or debugging task.'
last_reviewed: 2026-04-22
reviewer: xiaosongz
---

## Overview

The DATA step is a row-at-a-time iteration over input data with an
implicit `OUTPUT` at the bottom and a Program Data Vector (PDV) that
carries state across rows only for `RETAIN`ed variables. Most "silent
bug" DATA steps are scope errors: a variable that should be retained is
not, a MERGE silently overwrites one side with another, a `LAG` is
positioned inside a conditional, or a quoted macro trigger resolves at
an unexpected phase. This file encodes the DATA-step-semantic rules —
MERGE silent overwrite, LAG queue, PROC APPEND shape, SQL-vs-MERGE
distinction, macro / quote resolution, and RETAIN discipline — drawn
from `jphall663/GWU_data_mining` (see
`pipeline/manual/gwu-data-mining-5-items.md`) and `sasjs/core` v4.63.0.
File hygiene conventions from `sasjs/lint` v2.4.3 (indentation,
line-length, tabs, trailing whitespace, gremlins, encoded passwords)
appear in a trailing `## File hygiene (sasjs/lint)` section so the
DATA-step semantics lead the file.

## Critical Rules

### Rule 1: MERGE silently overwrites same-named columns — rename on input, then coalesce (GWU §2)

Source: https://github.com/jphall663/GWU_data_mining — hand-transcribed in `pipeline/manual/gwu-data-mining-5-items.md`.

`MERGE a b; BY id;` silently lets `b.var` overwrite `a.var` whenever both
sides carry the same variable name with different values. The SAS log
issues no diagnostic. Rename each side's payload columns on input, then
`coalesce` explicitly in the body of the step.

```sas
/* CORRECT — rename on the way in, then coalesce explicitly */
data members_all;
  merge elig(rename=(paid_amt=paid_amt_elig))
        claims(rename=(paid_amt=paid_amt_clm));
  by member_id;
  paid_amt = coalesce(paid_amt_clm, paid_amt_elig);
run;
```

```sas
/* WRONG — claims.paid_amt silently overwrites elig.paid_amt on shared member_id */
data members_all;
  merge elig claims;
  by member_id;
run;
```

### Rule 2: LAG is queue-based — call unconditionally, then gate usage (GWU §1)

Source: https://github.com/jphall663/GWU_data_mining — hand-transcribed in `pipeline/manual/gwu-data-mining-5-items.md`.

`LAG(x)` returns the value from the previous *CALL* to `LAG`, not the
previous *observation*. Placing `LAG` inside a conditional advances its
queue only on matching rows, so the lagged value ends up coming from an
arbitrary earlier row rather than the immediately preceding one. Always
call `LAG` unconditionally, then gate how the result is used.

```sas
/* CORRECT — always advance the lag queue; gate usage afterwards */
data claims_lagged;
  set claims;
  by member_id service_dt;
  prev_paid = lag(paid_amt);                 /* unconditional queue advance */
  if not first.member_id then paid_delta = paid_amt - prev_paid;
run;
```

```sas
/* WRONG — prev_paid queue advances only on non-first rows; lag is misaligned */
data claims_lagged;
  set claims;
  by member_id service_dt;
  if not first.member_id then prev_paid = lag(paid_amt);
run;
```

### Rule 3: PROC APPEND variable-shape rules — missing-from-BASE ERRORs, missing-from-DATA silently nulls (GWU §3)

Source: https://github.com/jphall663/GWU_data_mining — hand-transcribed in `pipeline/manual/gwu-data-mining-5-items.md`.

`PROC APPEND BASE=a DATA=b` uses BASE's variable definitions. Without
`FORCE`, any variable in DATA= that is absent from BASE= causes the step
to **fail with ERROR** — nothing is appended. With `FORCE`, the extra
variable is **dropped with a WARNING**. The silent mode is different:
when BASE= carries a variable absent from DATA=, appended rows get
missing values in that column, with no diagnostic — easy to miss when
BASE= has been recently extended.

```sas
/* CORRECT — explicitly reshape DATA to match BASE before appending */
data claims_new_aligned;
  set claims_new;
  keep member_id service_dt paid_amt dx_code;   /* whatever BASE=claims has */
run;
proc append base=claims data=claims_new_aligned;   /* no FORCE needed */
run;

/* or: use FORCE only when knowingly dropping new columns */
proc append base=claims data=claims_new force;     /* drops new-in-DATA vars w/ WARNING */
run;
```

```sas
/* WRONG — DATA has a column absent from BASE; step errors without FORCE */
proc append base=claims data=claims_new;
run;
/* ERROR: Variable ndc_code in DATA set not in BASE set. No appending done. */

/* Subtler silent mode: BASE has a column absent from DATA */
proc append base=claims_v2 data=claims_v1;   /* v2 added ndc_code; v1 lacks it */
run;
/* Step succeeds; ndc_code is missing for every v1 row — no WARNING. */
```

### Rule 4: SQL join vs MERGE — different semantics, different failure modes; use explicit `coalesce` in joins (GWU §4)

Source: https://github.com/jphall663/GWU_data_mining — hand-transcribed in `pipeline/manual/gwu-data-mining-5-items.md`.

DATA-step MERGE requires sorted BY variables and right-overwrites
silently; PROC SQL joins do not require sorting, but `a.*, b.*` in the
select list produces ambiguous same-named columns and — on unqualified
`FROM a, b` without a `WHERE` — a silent Cartesian product. Qualify every
shared column and use `COALESCE` to pick a single value explicitly.

```sas
/* CORRECT — qualify each column; coalesce shared payloads explicitly */
proc sql;
  create table members_all as
  select
      a.member_id,
      coalesce(a.paid_amt, b.paid_amt) as paid_amt,
      a.service_dt,
      b.dx_code
  from elig as a
  full join claims as b
    on a.member_id = b.member_id;
quit;
```

```sas
/* WRONG — unqualified select *, comma-join with no WHERE; silent Cartesian */
proc sql;
  create table members_all as
  select a.*, b.*
  from elig as a, claims as b;   /* no ON / no WHERE — every elig row × every claim row */
quit;
```

### Rule 5: Macro resolution and quote semantics — DATA-step single-vs-double quotes, macro-context masks via `%nrstr` (GWU §5)

Source: https://github.com/jphall663/GWU_data_mining — hand-transcribed in `pipeline/manual/gwu-data-mining-5-items.md`.

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

### Rule 6: Retain accumulators and carry-forward variables — or they reset to missing each iteration

Source: https://github.com/sasjs/core/blob/3a54b9c796c0bfe477d1aefc1e22b9ff9f2c96c2/base/mp_hashdataset.sas

A DATA step reinitializes every non-RETAINed PDV slot to missing on each
iteration. An accumulator of the form `cum = cum + x;` therefore computes
`missing + x = missing` every row unless `cum` is retained with an
explicit initial value. The `sasjs/core` `mp_hashdataset.sas` macro
illustrates the pattern (`retain &prevkeyvar;`) when carrying state
across rows.

```sas
/* CORRECT — retain the accumulator with an explicit initial value */
data claims_running;
  set claims;
  by member_id;
  retain cum_paid 0;
  if first.member_id then cum_paid = 0;
  cum_paid = cum_paid + paid_amt;
run;
```

```sas
/* WRONG — cum_paid is not retained; every row computes missing + paid_amt = missing */
data claims_running;
  set claims;
  cum_paid = cum_paid + paid_amt;
run;
```

## Canonical Idioms

### Idiom: Guarded predicate macro for DATA-step assertions

Source: https://github.com/sasjs/core/blob/3a54b9c796c0bfe477d1aefc1e22b9ff9f2c96c2/base/mp_assertdsobs.sas

Purpose: a one-liner test that appends PASS/FAIL rows to a shared
results dataset — lets an analyst sprinkle assertions across a long DATA
step pipeline without interrupting the flow.

```sas
/* Usage — no observations test */
%mp_assertdsobs(work.claims_clean)

/* Usage — row-count test */
%mp_assertdsobs(work.claims_clean, test=ATLEAST 1000,
  desc=claims_clean row-count sanity check)
```

### Idiom: `mf_nobs` — observation-count one-liner for open code

Source: https://github.com/sasjs/core/blob/3a54b9c796c0bfe477d1aefc1e22b9ff9f2c96c2/base/mf_nobs.sas

Purpose: quick `NLOBS` read-out via `attrn`. Useful inside `%if` gates and
PUTLOG diagnostics. The macro is a thin wrapper around `%mf_getattrn`.

```sas
%put Number of observations=%mf_nobs(sashelp.class);
%if %mf_nobs(work.claims_clean) = 0 %then %do;
  %put WARNING- claims_clean is empty, aborting step.;
  %return;
%end;
```

## Function / Statement Quick Ref

| Name | Syntax | Purpose | Common mistake | Doc URL |
|------|--------|---------|----------------|---------|
| `set` | `set ds1 ds2 ...;` | Read input datasets into PDV | Omitting `by` for MERGE-alternative interleave | [`set`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lestmtsref&docsetTarget=titlepage.htm) |
| `merge` | `merge a b; by id;` | BY-group DATA-step join | Right-side silently overwrites (see Rule 1 / GWU §2) | [`merge`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lestmtsref&docsetTarget=titlepage.htm) |
| `by` | `by var1 var2;` | Group boundary for MERGE / `first.` / `last.` | Inputs not pre-sorted on BY vars | [`by`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lestmtsref&docsetTarget=titlepage.htm) |
| `retain` | `retain var initial;` | Carry a PDV value across iterations | Forgetting `retain` → accumulator resets to missing each row (see Rule 6) | [`retain`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lestmtsref&docsetTarget=titlepage.htm) |
| `array` | `array a{10} a1-a10;` | Declare a DATA-step array | Using `{}` vs `()` inconsistently; mismatched bounds | [`array`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lestmtsref&docsetTarget=titlepage.htm) |
| `do` / `end` | `do i = 1 to n; ... end;` | Iterative loop in DATA step | Using DATA `do` vs macro `%do` | [`do` / `end`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lestmtsref&docsetTarget=titlepage.htm) |
| `output` | `output <dsname>;` | Explicit write of the current PDV | Using `output` inside `if` without covering all branches | [`output`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lestmtsref&docsetTarget=titlepage.htm) |
| `keep` | `keep var1 var2;` | Restrict output columns | Placing `keep=` on dataset option vs statement form | [`keep`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lestmtsref&docsetTarget=titlepage.htm) |
| `drop` | `drop var1 var2;` | Drop output columns | `drop` a BY variable — breaks downstream merges | [`drop`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lestmtsref&docsetTarget=titlepage.htm) |
| `rename` | `rename old=new;` or `ds(rename=(old=new))` | Rename on input or output | Using in-statement rename when in-dataset-option rename is safer | [`rename`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lestmtsref&docsetTarget=titlepage.htm) |
| `format` | `format var mmddyy10.;` | Attach a format to a variable | Forgetting trailing `.` in format name | [`format`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lestmtsref&docsetTarget=titlepage.htm) |
| `length` | `length var $32;` | Declare column length / type | Omitting → char defaults to first-assignment length, often 8 | [`length`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lestmtsref&docsetTarget=titlepage.htm) |
| `attrib` | `attrib var length=$32 format=$32. label='...';` | Combined length/format/label | Using `attrib` when `length` alone would do | [`attrib`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lestmtsref&docsetTarget=titlepage.htm) |
| `call missing` | `call missing(a, b, c);` | Set multiple vars to missing | Using `a = .; b = .;` instead for >2 vars | [`call missing`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| `_N_` | automatic var | Current iteration count | Treating as row number after `set`+`where` filter | [`Automatic Variables`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lepg&docsetTarget=titlepage.htm) |
| `_ERROR_` | automatic var | Flag: 1 if any data error this row | Not resetting with `_ERROR_ = 0;` after handling | [`Automatic Variables`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lepg&docsetTarget=titlepage.htm) |
| `lag` | `lag(x)` | Queue-based previous-call value | Placing inside conditional → misaligned queue (see Rule 2 / GWU §1) | [`lag`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| `coalesce` | `coalesce(a, b, c)` | First non-missing value | Forgetting it's non-short-circuit — all args evaluated | [`coalesce`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| `symget` | `symget('macvar')` | Read macro var at DATA-step *execute* time | Using when compile-time `&macvar` would work | [`symget`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| `call symputx` | `call symputx('macvar', value, 'G'|'L'|'F');` | Write a macro var from DATA step | Omitting scope — surprises in nested contexts | [`call symputx`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |

## Silent Pitfalls

- **MERGE overwrite** — same-named variable on both sides silently takes
  the right-side value. See Rule 1 and
  `pipeline/manual/gwu-data-mining-5-items.md` §2.
  Source: https://github.com/jphall663/GWU_data_mining

- **LAG inside IF** — `LAG` advances its queue only when called; a
  conditional call misaligns the lag value. See Rule 2 and GWU §1.
  Source: https://github.com/jphall663/GWU_data_mining

- **`retain` forgotten for accumulator** — `data out; set in; cum = cum +
  x; run;` without `retain cum 0;` — `cum` resets to missing each row,
  and missing + x = missing. Always `retain` accumulators with an
  explicit initial value. See Rule 6.
  Source: https://github.com/sasjs/core/blob/3a54b9c796c0bfe477d1aefc1e22b9ff9f2c96c2/base/mp_hashdataset.sas
  (example of `retain &prevkeyvar;` for cross-row state).

- **PROC APPEND mismatched-shape modes** — without `FORCE`, a column in
  DATA= absent from BASE= ERRORs (step fails, nothing appended); with
  `FORCE` the extra column drops with a WARNING. The silent mode is
  BASE-has-extra: appended rows get missing values in that column, no
  diagnostic. See Rule 3 and GWU §3.
  Source: https://github.com/jphall663/GWU_data_mining

- **Macro-context quote masking** — single-quoted `%put '&var'` still
  resolves `&var` because the macro processor tokenizes before the
  statement receives its argument. Use `%nrstr(...)` to mask triggers.
  See Rule 5 and GWU §5.
  Source: https://github.com/jphall663/GWU_data_mining

- **Trailing spaces / tabs / gremlins** — invisible-character bugs in
  `where` clauses and string literals. Enforce via `sasjs/lint`
  `noTabs`, `noTrailingSpaces`, `noGremlins` (see File hygiene
  Hygiene 3–5).

## Anti-patterns (STOP signs)

**STOP** when you see any of the following — the code compiles and
produces output, but the output is almost certainly wrong:

- `merge a b; by id; run;` with shared payload column names → see
  Rule 1 / GWU §2.
- `if cond then lagx = lag(x);` → see Rule 2 / GWU §1.
- `data out; set in; cum = cum + x; run;` with no `retain cum 0;` → see
  Rule 6.
- `proc append base=a data=b;` where `b` has a column not in `a`, no
  `FORCE` specified → step ERRORs, nothing appended; see Rule 3 / GWU §3.
- `select a.*, b.*` in a PROC SQL join where `a` and `b` share column
  names other than the join key → ambiguous; see Rule 4 / GWU §4.
- `%put '&var';` expecting single quotes to suppress macro resolution →
  see Rule 5 / GWU §5.

## File hygiene (sasjs/lint)

File-hygiene items from `sasjs/lint` v2.4.3. These are line-level
conventions — indentation, line length, whitespace, non-printables,
encoded passwords — that do not alter DATA-step semantics but do cause
review-time churn or invisible-byte bugs when left unchecked. Kept here
as `### Hygiene N:` entries so the semantic DATA-step Rules above
dominate the top of the file; each hygiene item still carries its
upstream Source URL and a CORRECT / WRONG example.

### Hygiene 1: Indent by a consistent multiple of spaces (default 2) — no ad-hoc indentation

Source: https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/line/indentationMultiple.ts

`sasjs/lint indentationMultiple` fires when a line is indented by a
non-multiple of the configured width (default 2). Consistent indentation
makes DATA-step / macro nesting readable at a glance.

```sas
/* CORRECT - indented by 2 */
data out;
  set in;
  if x > 0 then y = log(x);
run;
```

```sas
/* WRONG - indented by 1 or 3 spaces */
data out;
 set in;
   if x > 0 then y = log(x);
run;
```

### Hygiene 2: Keep lines under the configured maximum length (default 300)

Source: https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/line/maxLineLength.ts

`sasjs/lint maxLineLength` flags any line exceeding the configured limit.
Long lines hide logic in horizontal scroll and break diff review. For
long variable lists, break after a comma; for long `where` clauses,
break after the logical operator.

```sas
/* CORRECT - wrap after comma / logical op */
data claims_2023;
  set raw.claims;
  where service_dt between '01JAN2023'd and '31DEC2023'd
    and paid_amt > 0
    and not missing(member_id);
run;
```

```sas
/* WRONG - one 300+ char line with all conditions inline */
data claims_2023; set raw.claims; where service_dt between '01JAN2023'd and '31DEC2023'd and paid_amt > 0 and not missing(member_id) and provider_npi ne '' and diagnosis_code in ('E11.9','I10','N18.3','J44.9'); run;
```

### Hygiene 3: Indent with spaces, never tab characters

Source: https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/line/noTabs.ts

`sasjs/lint noTabs` rejects any `\t` (ASCII 0x09). Tab rendering depends
on editor settings — what looks aligned on one machine is misaligned on
another and confuses diff tools.

```sas
/* CORRECT - two spaces */
data out;
  set in;
run;
```

```sas
/* WRONG - leading tab; noTabs fires */
data out;
	set in;
run;
```

### Hygiene 4: Strip trailing whitespace from every line

Source: https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/line/noTrailingSpaces.ts

`sasjs/lint noTrailingSpaces` flags any line ending with one or more
spaces before the newline. Trailing spaces break `diff --word-diff` and
cause spurious merge conflicts.

```sas
/* CORRECT - no trailing space */
data out;
  set in;
run;
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

### Hygiene 5: No "gremlin" non-printable characters

Source: https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/line/noGremlins.ts

`sasjs/lint noGremlins` flags characters outside the standard printable
ASCII + allowed-list Unicode range. Invisible characters in a `where`
clause or string literal break equality compares at runtime with no log
diagnostic.

```sas
/* CORRECT - plain ASCII */
data out;
  set in;
  where member_id = 'A12345';
run;
```

```sas
/* WRONG - gremlin bytes inside the quoted string (invisible in most editors)

   The literal bytes between 'A' and '12345' below include U+FEFF (BOM,
   three bytes: EF BB BF) copied from an Excel export. `sasjs/lint noGremlins`
   flags the token; the WHERE clause silently fails to match cleanly-typed
   'A12345' rows.
*/
data out;
  set in;
  where member_id = 'A<U+FEFF>12345';   /* actual file would have invisible bytes */
run;
```

### Hygiene 6: Never commit encoded-password literals (`{SAS001}`, `{SAS002}`, `{SASENC}`)

Source: https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/line/noEncodedPasswords.ts

`sasjs/lint noEncodedPasswords` fires on any line containing the
bracketed encoding markers. SAS encoded passwords are trivially
reversible — they are obfuscation, not encryption. Treat them as
plaintext for secret-management purposes.

```sas
/* CORRECT - read password from env or autoexec, never in source */
libname db oracle user=svc password="&env_db_pw" path=prod;
```

```sas
/* WRONG - committed to source; noEncodedPasswords fires */
libname db oracle user=svc password="{SAS002}D41D8CD98F00B204E9800998ECF8427E" path=prod;
```

## See Also

- [sas-master-reference.md](sas-master-reference.md) — top-20 aggregated
  rules; start here for new `.sas` files.
- [macros.md](macros.md) — macro-side of `call symputx` / `symget` /
  macro-generated DATA-step code.
- [proc-sql.md](proc-sql.md) — SQL-join side of Rule 4 / GWU §4.
- [hash-tables.md](hash-tables.md) — hash-lookup alternative to MERGE for
  reference-table joins.
- [functions-dates.md](functions-dates.md) — date/time functions
  (INTNX, INTCK, MDY, DATEPART) used alongside DATA-step logic.
- [functions-strings.md](functions-strings.md) — string functions
  (SCAN, SUBSTR, CATX, COMPRESS) used in DATA-step parsing.
- [functions-numeric.md](functions-numeric.md) — numeric and array
  functions (SUM, ROUND, MOD, DIM) for row-wise arithmetic.
- `pipeline/manual/gwu-data-mining-5-items.md` — upstream GWU
  transcription feeding Rules 1–5.
