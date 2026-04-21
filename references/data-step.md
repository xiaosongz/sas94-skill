---
title: DATA step reference
scope: MERGE / BY processing, `first.`/`last.`, `retain`, arrays, PDV initialization, and DATA-step iteration semantics.
loaded_when: '"MERGE", "BY processing", "first.", "last.", "retain", "array", "PDV", or any DATA-step authoring or debugging task.'
last_reviewed: 2026-04-21
reviewer: xiaosongz
---

## Overview

The DATA step is a row-at-a-time iteration over input data with an
implicit `OUTPUT` at the bottom and a Program Data Vector (PDV) that
carries state across rows only for `RETAIN`ed variables. Most "silent
bug" DATA steps are scope errors: a variable that should be retained is
not, a MERGE silently overwrites one side with another, or a `LAG` is
positioned inside a conditional. This file encodes the line-level and
file-level conventions from `sasjs/lint` v2.4.3, the DATA-step-oriented
helper idioms from `sasjs/core` v4.63.0, and five hand-transcribed
pitfalls from `jphall663/GWU_data_mining` (see
`pipeline/manual/gwu-data-mining-5-items.md`).

## Critical Rules

### Rule 1: Indent by a consistent multiple of spaces (default 2) — no ad-hoc indentation

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

### Rule 2: Keep lines under the configured maximum length (default 300)

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

### Rule 3: Indent with spaces, never tab characters

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

### Rule 4: Strip trailing whitespace from every line

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
/* WRONG - two trailing spaces on the %put line */
data out;
  set in;
%put 'hello';··
run;
```

### Rule 5: No "gremlin" non-printable characters

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
/* WRONG - zero-width no-break space inside 'A12345' */
data out;
  set in;
  where member_id = 'A12345';  /* contains invisible U+FEFF */
run;
```

### Rule 6: Never commit encoded-password literals (`{SAS001}`, `{SAS002}`, `{SASENC}`)

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

### Idiom: LAG missing-value trap (GWU §1)

Source: https://github.com/jphall663/GWU_data_mining — hand-transcribed in `pipeline/manual/gwu-data-mining-5-items.md`.

Purpose: `LAG(x)` returns the value from the previous *CALL* to LAG, not
the previous *observation*. Placing `LAG` inside a conditional breaks the
queue — always call LAG unconditionally, then gate the usage.

```sas
/* CORRECT — always call lag; gate usage afterwards */
data out;
  set in;
  prev_x = lag(x);                 /* unconditional queue advance */
  if month = 1 then lag_x = prev_x;
run;
```

```sas
/* WRONG — lag_x not aligned with previous row */
data out;
  set in;
  if month = 1 then lag_x = lag(x);  /* queue advances only on Jan */
run;
```

### Idiom: MERGE overwrite trap (GWU §2)

Source: https://github.com/jphall663/GWU_data_mining — hand-transcribed in `pipeline/manual/gwu-data-mining-5-items.md`.

Purpose: `MERGE a b; BY id;` silently lets `b.var` overwrite `a.var` when
both sides carry the same variable name with different values. Rename
on the way in, then coalesce.

```sas
/* CORRECT - rename on the way in, then keep explicitly */
data both;
  merge a(rename=(amount=amount_a))
        b(rename=(amount=amount_b));
  by id;
  amount = coalesce(amount_a, amount_b);
run;
```

```sas
/* WRONG - b.amount silently overwrites a.amount */
data both;
  merge a b;
  by id;
run;
```

### Idiom: PROC APPEND base-set rule (GWU §3)

Source: https://github.com/jphall663/GWU_data_mining — hand-transcribed in `pipeline/manual/gwu-data-mining-5-items.md`.

Purpose: `PROC APPEND BASE=a DATA=b;` uses BASE as the schema contract.
Columns present in DATA but not BASE are dropped silently without
`FORCE`. Always pre-define BASE's schema, or add explicit `LENGTH`
statements.

```sas
/* CORRECT - add missing columns to base first */
data a;
  set a;
  length new_col $32;
run;
proc append base=a data=b; run;  /* now keeps new_col */
```

```sas
/* WRONG - new_col in b is silently dropped */
proc append base=a data=b; run;
```

### Idiom: SQL join vs MERGE distinction (GWU §4)

Source: https://github.com/jphall663/GWU_data_mining — hand-transcribed in `pipeline/manual/gwu-data-mining-5-items.md`.

Purpose: DATA-step MERGE requires sorted BY and right-overwrites silently;
PROC SQL join does not require sorting and leaves unmatched rows null.
Use SQL's `COALESCE` to merge same-named columns explicitly.

```sas
/* CORRECT - qualify or coalesce every shared column */
proc sql;
  create table t as
  select a.id, coalesce(a.amount, b.amount) as amount
  from a full join b on a.id = b.id;
quit;
```

```sas
/* WRONG - ambiguous shared columns, silent Cartesian risk */
proc sql;
  create table t as
  select a.*, b.*
  from a inner join b on a.id = b.id;
quit;
```

### Idiom: Macro-quote `'` vs `"` (GWU §5)

Source: https://github.com/jphall663/GWU_data_mining — hand-transcribed in `pipeline/manual/gwu-data-mining-5-items.md`.

Purpose: single quotes suppress macro resolution; double quotes resolve
`&var`. `%str('text')` does NOT unquote the inner `&var`. Use `%nrstr` to
explicitly hold `&` and `%` triggers literal.

```sas
/* CORRECT - double quotes resolve &name */
%let name = claims;
%put "table: &name";                /* prints: table: claims */
%put %nrstr(literal &name unresolved); /* prints: literal &name unresolved */
```

```sas
/* WRONG - single quotes block resolution */
%let name = claims;
%put 'table: &name';                 /* prints: table: &name */
```
## Function / Statement Quick Ref

| Name | Syntax | Purpose | Common mistake | Doc URL |
|------|--------|---------|----------------|---------|
| `set` | `set ds1 ds2 ...;` | Read input datasets into PDV | Omitting `by` for MERGE-alternative interleave | TODO (source pending) |
| `merge` | `merge a b; by id;` | BY-group DATA-step join | Right-side silently overwrites (see Rule / GWU §2) | TODO (source pending) |
| `by` | `by var1 var2;` | Group boundary for MERGE / `first.` / `last.` | Inputs not pre-sorted on BY vars | TODO (source pending) |
| `retain` | `retain var initial;` | Carry a PDV value across iterations | Forgetting `retain` → accumulator resets to missing each row | TODO (source pending) |
| `array` | `array a{10} a1-a10;` | Declare a DATA-step array | Using `{}` vs `()` inconsistently; mismatched bounds | TODO (source pending) |
| `do` / `end` | `do i = 1 to n; ... end;` | Iterative loop in DATA step | Using DATA `do` vs macro `%do` | TODO (source pending) |
| `output` | `output <dsname>;` | Explicit write of the current PDV | Using `output` inside `if` without covering all branches | TODO (source pending) |
| `keep` | `keep var1 var2;` | Restrict output columns | Placing `keep=` on dataset option vs statement form | TODO (source pending) |
| `drop` | `drop var1 var2;` | Drop output columns | `drop` a BY variable — breaks downstream merges | TODO (source pending) |
| `rename` | `rename old=new;` or `ds(rename=(old=new))` | Rename on input or output | Using in-statement rename when in-dataset-option rename is safer | TODO (source pending) |
| `format` | `format var mmddyy10.;` | Attach a format to a variable | Forgetting trailing `.` in format name | TODO (source pending) |
| `length` | `length var $32;` | Declare column length / type | Omitting → char defaults to first-assignment length, often 8 | TODO (source pending) |
| `attrib` | `attrib var length=$32 format=$32. label='...';` | Combined length/format/label | Using `attrib` when `length` alone would do | TODO (source pending) |
| `call missing` | `call missing(a, b, c);` | Set multiple vars to missing | Using `a = .; b = .;` instead for >2 vars | TODO (source pending) |
| `_N_` | automatic var | Current iteration count | Treating as row number after `set`+`where` filter | TODO (source pending) |
| `_ERROR_` | automatic var | Flag: 1 if any data error this row | Not resetting with `_ERROR_ = 0;` after handling | TODO (source pending) |
| `lag` | `lag(x)` | Queue-based previous-call value | Placing inside conditional → misaligned queue (GWU §1) | TODO (source pending) |
| `coalesce` | `coalesce(a, b, c)` | First non-missing value | Forgetting it's non-short-circuit — all args evaluated | TODO (source pending) |
| `symget` | `symget('macvar')` | Read macro var at DATA-step *execute* time | Using when compile-time `&macvar` would work | TODO (source pending) |
| `call symputx` | `call symputx('macvar', value, 'G'|'L'|'F');` | Write a macro var from DATA step | Omitting scope — surprises in nested contexts | TODO (source pending) |

## Silent Pitfalls

- **MERGE overwrite** — same-named variable on both sides silently takes
  the right-side value. See Canonical Idiom "MERGE overwrite trap" and
  `pipeline/manual/gwu-data-mining-5-items.md` §2.
  Source: https://github.com/jphall663/GWU_data_mining

- **LAG inside IF** — `LAG` advances its queue only when called; a
  conditional call misaligns the lag value. See Canonical Idiom "LAG
  missing-value trap" and GWU §1.
  Source: https://github.com/jphall663/GWU_data_mining

- **`retain` forgotten for accumulator** — `data out; set in; cum = cum +
  x; run;` without `retain cum 0;` — `cum` resets to missing each row,
  and missing + x = missing. Always `retain` accumulators with an
  explicit initial value.
  Source: https://github.com/sasjs/core/blob/3a54b9c796c0bfe477d1aefc1e22b9ff9f2c96c2/base/mp_hashdataset.sas
  (example of `retain &prevkeyvar;` for cross-row state).

- **PROC APPEND drops columns silently without FORCE** — see Canonical
  Idiom "PROC APPEND base-set rule" and GWU §3.
  Source: https://github.com/jphall663/GWU_data_mining

- **Trailing spaces / tabs / gremlins** — invisible-character bugs in
  `where` clauses and string literals. Enforce via `sasjs/lint`
  `noTabs`, `noTrailingSpaces`, `noGremlins` (see Rules 3–5).

## Anti-patterns (STOP signs)

**STOP** when you see any of the following — the code compiles and
produces output, but the output is almost certainly wrong:

- `merge a b; by id; run;` without `first.id` / `last.id` handling on a
  key that is duplicated in either side → see MERGE overwrite; GWU §2.
- `if cond then lagx = lag(x);` → see LAG-inside-IF; GWU §1.
- `data out; set in; cum = cum + x; run;` with no `retain cum 0;` → see
  Silent Pitfalls.
- `proc append base=a data=b;` where `b` has a column not in `a`, no
  `FORCE` specified → column dropped silently; GWU §3.
- `select a.*, b.*` in a PROC SQL join where `a` and `b` share column
  names other than the join key → ambiguous; GWU §4.

## See Also

- [sas-master-reference.md](sas-master-reference.md) — top-20 aggregated
  rules; start here for new `.sas` files.
- [macros.md](macros.md) — macro-side of `call symputx` / `symget` /
  macro-generated DATA-step code.
- [proc-sql.md](proc-sql.md) — SQL-join side of GWU §4 distinction
  (Phase 2+).
- [hash-tables.md](hash-tables.md) — hash-lookup alternative to MERGE for
  reference-table joins (Phase 2+).
- [functions-reference.md](functions-reference.md) — `lag`, `coalesce`,
  `call missing`, `_N_`, `_ERROR_` signatures (Phase 2+).
