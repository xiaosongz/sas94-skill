---
title: SAS functions reference
scope: Function-signature cheatsheet organized by category — date arithmetic, string manipulation, numeric, array, and macro-aware functions. Focused on argument-order traps and default-behavior pitfalls that produce silent bugs in claims-data pipelines.
loaded_when: '"function", "date arithmetic", "INTNX", "INTCK", "SCAN", "SUBSTR", "SUBSTRN", "CATX", "CATS", "COMPRESS", "ROUND", "MOD", "SUM function", "DIM", "%SYSFUNC", or any function-signature / function-semantics question.'
last_reviewed: 2026-04-21
reviewer: xiaosongz
---

## Overview

The DATA-step function library is where most subtle SAS bugs live:
default arguments, sign conventions, and "is it a decimal place or a
rounding unit" semantics that differ from the equivalents in R / Python
/ SQL. A `SCAN(text, 3)` call that worked on one dataset can silently
break on the next because SAS's default delimiter list includes the
comma *and* the period *and* the parenthesis — none of which the author
thought of as delimiters. An `INTNX('month', dt, 0)` call returns the
first of the month, not `dt`, because the default alignment is
`BEGINNING`. A `MOD(-7, 3)` returns `-1`, not `2`, because SAS's MOD
uses sign-of-dividend.

This file encodes the signatures and gotchas for the ~35 functions
that cover 90% of claims-data DATA-step work: date/time arithmetic
(`INTCK`, `INTNX`, `MDY`, `DATEPART`, `YEAR`/`MONTH`/`DAY`), string
manipulation (`SCAN`, `SUBSTR`/`SUBSTRN`, `CATX`, `COMPRESS`,
`TRANWRD`, `FIND`/`INDEX`), numeric (`SUM`, `ROUND`, `MOD`, `MEAN`),
array inspection (`DIM`, `HBOUND`/`LBOUND`), and the macro-context
bridges (`%SYSFUNC`, `%SCAN`, `%SUBSTR`). Every rule and idiom cites
`SAS Functions and CALL Routines: Reference` (lefunctionsref.htm), the
primary reference; the cached Markdown is at
`pipeline/cache/docs/lefunctionsref.md` (338K words).

For DATA-step statement-level reference (MERGE, BY, RETAIN, arrays as
declarations) see `data-step.md`; for macro-language authoring see
`macros.md`; for PROC-level summary stats (MAX / MEAN as aggregates
rather than row-wise) see `base-procs.md` and `proc-sql.md`.

## Critical Rules

### Rule 1: `SCAN(str, n)` without an explicit delimiter uses SAS's default delimiter set — which includes comma, period, and parentheses

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm

With only two arguments, SCAN uses the environment's default delimiter
list. On ASCII systems that list is
`blank ! $ % & ( ) * + , - . / ; < ^ |` — so `SCAN('Smith, John', 1)`
returns `Smith`, not `Smith, John`. For any string containing
punctuation, always pass the third `character-list` argument explicitly.

```sas
/* CORRECT - explicit delimiter; only "|" splits words */
data dx; set raw_dx;
  primary_dx = scan(dx_list, 1, '|');
run;
```

```sas
/* WRONG - default delimiters include comma, dot, parens, slash */
data dx; set raw_dx;
  primary_dx = scan(dx_list, 1);   /* 'I10.9|I11.0' -> 'I10', not 'I10.9' */
run;
```

### Rule 2: `SUBSTR` errors on nonpositive position; `SUBSTRN` returns a zero-length result instead — prefer `SUBSTRN` when position can be ≤ 0

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm

`SUBSTR(str, -1, 5)` writes a note to the log, sets `_ERROR_ = 1`, and
returns the substring from position 1 to end of string. `SUBSTRN(str,
-1, 5)` silently truncates to the first valid character. When position
is driven by a `FIND` result or arithmetic that may underflow, use
`SUBSTRN` — it degrades to empty/zero-length instead of poisoning the
step with `_ERROR_=1`.

```sas
/* CORRECT - SUBSTRN degrades to "" when find() returns 0 */
data parsed; set raw;
  hyphen = find(member_id, '-');
  suffix = substrn(member_id, hyphen + 1, 4);
run;
```

```sas
/* WRONG - SUBSTR with position 1 when hyphen=0 sets _ERROR_=1 */
data parsed; set raw;
  hyphen = find(member_id, '-');
  suffix = substr(member_id, hyphen + 1, 4);
run;
```

### Rule 3: `INTNX('interval', dt, 0)` with no `alignment` returns the **beginning** of the interval, not `dt` — use `'S'` (SAME) for same-day alignment

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm

The fourth argument `alignment` defaults to `BEGINNING`. So
`intnx('month', service_dt, 0)` returns the first of `service_dt`'s
month, not `service_dt` itself. For "shift by N months but keep the
day-of-month" semantics use `'SAME'` (alias `'S'`). A common claims
bug: computing `months_since_start = intck('month', a, b)` and then
trying to reconstruct the corresponding date with `intnx('month', a,
k)` — which lands on the first of each month, not the anniversary day.

```sas
/* CORRECT - SAME alignment preserves day-of-month */
data claims; set claims;
  anniversary = intnx('year', enroll_dt, 1, 'same');
run;
```

```sas
/* WRONG - default BEGINNING alignment; lands on 01JAN */
data claims; set claims;
  anniversary = intnx('year', enroll_dt, 1);   /* not what the name suggests */
run;
```

### Rule 4: `SUM(of x1-x5)` treats missing as zero; `x1+x2+x3+x4+x5` propagates missing — use `SUM` for missing-aware addition

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm

The `SUM` function returns the sum of **nonmissing** arguments; if all
arguments are missing the result is missing, but a single nonmissing
argument is enough to produce a number. The `+` operator propagates
missing: `.+ 3 = .`. For row-wise accumulation across optional
variables (e.g., per-diagnosis cost buckets that may be unset),
`SUM(of ...)` is almost always what you want.

```sas
/* CORRECT - missing treated as 0; total_paid is nonmissing if any bucket is */
data claims; set claims;
  total_paid = sum(of paid_ip paid_op paid_rx);
run;
```

```sas
/* WRONG - any missing bucket poisons the total */
data claims; set claims;
  total_paid = paid_ip + paid_op + paid_rx;   /* missing if any is missing */
run;
```

### Rule 5: `ROUND(x, unit)` rounds to the nearest **multiple of unit**, not to a number of decimal places

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm

`ROUND(3.14159, 1)` returns `3`. `ROUND(3.14159, 0.01)` returns `3.14`.
The second argument is a rounding unit, not a decimal-place count —
which trips up anyone coming from `round(x, digits)` in R or
`Math.round` with scaling. For "round to N decimals" use `ROUND(x,
10**(-n))` idiomatically, i.e. `ROUND(x, 0.01)` for two decimals.

```sas
/* CORRECT - 2 decimal rounding via unit=0.01 */
data claims; set claims;
  pmpm = round(total_paid / member_months, 0.01);
run;
```

```sas
/* WRONG - unit=2 rounds to nearest even integer */
data claims; set claims;
  pmpm = round(total_paid / member_months, 2);   /* nothing like 2-decimal rounding */
run;
```

### Rule 6: `COMPRESS(str, list, 'k')` **keeps** only chars in `list` — the `k` modifier inverts the default "remove" semantics

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm

With two arguments, `COMPRESS(str, '0123456789')` removes the listed
digits. Add the `'k'` modifier, `COMPRESS(str, '0123456789', 'k')`, and
the behavior inverts: everything **except** digits is removed. The
class modifiers (`'a'` alpha, `'d'` digit, `'p'` punctuation, `'s'`
space) compose with `'k'` to build "keep only alphanumerics"
one-liners, but mixing them up silently produces the opposite result.

```sas
/* CORRECT - keep only digits; strips everything else */
data claims; set claims;
  member_id_digits = compress(member_id, , 'kd');   /* k + d classes */
run;
```

```sas
/* WRONG - without 'k', removes the listed digits, keeps everything else */
data claims; set claims;
  member_id_digits = compress(member_id, '0123456789');   /* removes the digits */
run;
```

### Rule 7: `MOD(-7, 3)` returns `-1`, not `2` — SAS uses sign-of-dividend, not the mathematical modulo

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm

From the docs: "When the result is nonzero, the result has the same
sign as the first argument. The sign of the second argument is
ignored." This matches C's `%` operator, not Python's `%` or the
mathematical modulo-N that lives in [0, N). For claims work this
surfaces when computing "month-index modulo 12" with dates that land
on a negative SAS date integer, or when hashing a negative account key.
When you need the always-nonnegative version, use `mod(x, n) + n*(x<0)`
or rewrite as positive-first.

```sas
/* CORRECT - guard explicitly; never trust MOD on negatives */
data claims; set claims;
  bucket = mod(abs(acct_hash), 16);
run;
```

```sas
/* WRONG - relies on mathematical-modulo semantics; yields negative bucket */
data claims; set claims;
  bucket = mod(acct_hash, 16);   /* if acct_hash<0, bucket is negative */
run;
```

### Rule 8: `CATS`, `CATT`, and `CATX` differ in which blanks they strip — pick deliberately, don't reach for whichever you remember

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm

`CATS(a, b, c)` strips leading **and** trailing blanks from each
argument, no separator. `CATT(a, b, c)` strips only trailing blanks,
no separator. `CATX(sep, a, b, c)` strips leading and trailing blanks
from each argument and inserts `sep` between them — and silently
skips blank-only arguments so you don't get doubled separators. Default
output length is 200 for all three, which can silently truncate long
concatenations.

```sas
/* CORRECT - CATX is the right default for delimited keys */
data claims; set claims;
  length dedup_key $100;
  dedup_key = catx('|', member_id, put(service_dt, yymmdd10.), cpt);
run;
```

```sas
/* WRONG - CATS drops separator and glues everything together */
data claims; set claims;
  dedup_key = cats(member_id, service_dt, cpt);   /* "A12345215011234" */
run;
```

## Canonical Idioms

### Idiom: Month-end alignment for claims billing cycles

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm

Purpose: map every service date to the end of its calendar month for
PMPM / member-month aggregation. Use `INTNX` with `'E'` (END)
alignment — the last-day-of-month adjustment handles February and
leap years automatically, so there's no special case for 30- vs
31-day months.

```sas
data claims_eom; set claims;
  bill_eom   = intnx('month', service_dt, 0, 'e');   /* E = end-of-month */
  bill_start = intnx('month', service_dt, 0, 'b');   /* B = start-of-month */
run;
```

### Idiom: ICD-10 code prefix match with `SUBSTRN`

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm

Purpose: flag claims whose diagnosis starts with one of a set of
category codes (e.g., I10–I13 for hypertensive disease). `SUBSTRN`
tolerates codes shorter than 3 characters (returns empty) instead of
writing `_ERROR_=1`, which matters when the input column has nulls or
malformed entries from an upstream join.

```sas
data dx_flagged; set claims;
  icd_cat = substrn(icd10, 1, 3);
  if icd_cat in ('I10', 'I11', 'I12', 'I13') then hypertension = 1;
  else hypertension = 0;
run;
```

### Idiom: `CATX`-assembled composite key for dedup or merge

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm

Purpose: build a single-column composite key suitable for `PROC SORT
NODUPKEY`, hash-table lookups, or SQL joins. `CATX('|', ...)` handles
missing components by skipping them (no doubled separators) and strips
incidental padding. Put an explicit `length` on the output to avoid
the default 200-byte truncation for long keys.

```sas
data claims_keyed; set claims;
  length dedup_key $80;
  dedup_key = catx('|',
    member_id,
    put(service_dt, yymmdd10.),
    provider_npi,
    cpt_code);
run;
```

### Idiom: `%SYSFUNC` bridge — calling DATA-step functions from macro context

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm

Purpose: get a DATA-step function result into a macro variable without
a `DATA _NULL_` round-trip. `%sysfunc(today(), yymmdd10.)` returns
today's date as an ISO-formatted string. Watch for functions whose
arguments contain commas (`SCAN`, `SUBSTR`, `CATX`) — the macro
processor sees the inner commas as argument separators, so the call
must be masked with `%qscan`-style quoting or inline `%str(,)`.

```sas
/* run-date stamp for a dataset name */
%let rundate = %sysfunc(today(), yymmddn8.);
data claims_&rundate; set claims; run;

/* SCAN from macro context - inner comma needs protection */
%let tag = %sysfunc(scan(&list, 1, %str( )));
```

## Function / Statement Quick Ref

Single table with a category column — rows sorted by category, then
alphabetic within category. The Doc URL column is the single
`lefunctionsref.htm` docset landing page (per-function deep links are
not stable across docset revisions).

| Category | Name | Syntax | Purpose | Common mistake | Doc URL |
|----------|------|--------|---------|----------------|---------|
| date/time | `INTCK` | `intck('interval', d1, d2 <, 'method'>)` | Count interval boundaries between two dates | Default `method='DISCRETE'` counts boundaries; use `'CONTINUOUS'` for anniversary semantics | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| date/time | `INTNX` | `intnx('interval', d, n <, 'align'>)` | Shift date by N intervals | Default align=`'BEGINNING'`; use `'S'` for same-day (see Rule 3) | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| date/time | `TODAY` | `today()` | Current date (SAS date integer) | Embeds wall-clock — breaks reproducibility | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| date/time | `DATE` | `date()` | Alias for `today()` | Same reproducibility issue | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| date/time | `TIME` | `time()` | Seconds since midnight | Type is SAS time, not datetime | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| date/time | `DATETIME` | `datetime()` | Current SAS datetime value | Seconds since 01JAN1960 00:00 — not Unix epoch | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| date/time | `YEAR` | `year(d)` | Extract year from SAS date | Passing a datetime silently returns year-of-1960 offset | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| date/time | `MONTH` | `month(d)` | Extract month 1..12 from SAS date | Same datetime confusion as YEAR | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| date/time | `DAY` | `day(d)` | Extract day-of-month 1..31 | Same datetime confusion as YEAR | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| date/time | `QTR` | `qtr(d)` | Quarter 1..4 | SAS calendar quarters, not fiscal | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| date/time | `WEEKDAY` | `weekday(d)` | Day-of-week 1..7 (1=Sunday) | Many analysts expect 1=Monday | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| date/time | `MDY` | `mdy(m, d, y)` | Construct SAS date from m/d/y | Argument order is m-d-y (not ISO y-m-d) | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| date/time | `DATEPART` | `datepart(dt)` | SAS date from SAS datetime | Omitting it and using YEAR(dt) directly — wrong | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| date/time | `TIMEPART` | `timepart(dt)` | SAS time from SAS datetime | Discards date info silently | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| date/time | `DHMS` | `dhms(d, h, m, s)` | Compose datetime from d/h/m/s | Passing a datetime as the date arg | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| date/time | `DATDIF` | `datdif(d1, d2, basis)` | Day-count with basis ('ACT/ACT', '30/360') | Basis is required; not like INTCK('day') | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| string | `SCAN` | `scan(s, n <, delim <, mod>>)` | Extract nth word | Omitting delim uses default set — see Rule 1 | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| string | `SUBSTR` | `substr(s, pos <, len>)` | Extract fixed-position substring | Nonpositive pos sets `_ERROR_=1` — see Rule 2 | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| string | `SUBSTRN` | `substrn(s, pos <, len>)` | Safe substring — returns empty on bad pos | Silently empty when you expected content | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| string | `CATS` | `cats(a, b, ...)` | Concat, strip all blanks, no separator | Collapses values without separator — see Rule 8 | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| string | `CATT` | `catt(a, b, ...)` | Concat, strip trailing only | Leading blanks preserved — rarely what's wanted | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| string | `CATX` | `catx(sep, a, b, ...)` | Concat with separator, strip blanks | Default result length 200 — truncates long keys | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| string | `TRANWRD` | `tranwrd(s, old, new)` | Replace all occurrences of `old` with `new` | Case-sensitive; no regex | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| string | `COMPRESS` | `compress(s <, chars <, mod>>)` | Remove listed chars (or keep with `'k'`) | `'k'` modifier inverts meaning — see Rule 6 | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| string | `INDEX` | `index(s, sub)` | Position of first `sub`; 0 if absent | Case-sensitive; no wildcards | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| string | `FIND` | `find(s, sub <, mods <, start>>)` | Positional search with `'i'` case-insens mod | Forgetting `'i'` and missing mixed-case matches | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| string | `TRANSLATE` | `translate(s, to, from)` | Char-by-char swap | Argument order is `to, from` — opposite of tr(1) | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| string | `PROPCASE` | `propcase(s <, delims>)` | Title-case every word | Default delims include space, hyphen, tab | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| string | `UPCASE` | `upcase(s)` | ASCII uppercase | Not locale-aware | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| string | `LOWCASE` | `lowcase(s)` | ASCII lowercase | Not locale-aware | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| string | `STRIP` | `strip(s)` | Remove leading and trailing blanks | Not for interior whitespace | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| string | `TRIM` | `trim(s)` | Remove trailing blanks only | Leading blanks preserved; use STRIP for both sides | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| numeric | `SUM` | `sum(of x1-xN)` | Sum ignoring missing | Missing treated as 0 — see Rule 4 | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| numeric | `MEAN` | `mean(of x1-xN)` | Row-wise mean of nonmissing | Uses nonmissing count as denominator | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| numeric | `MEDIAN` | `median(of x1-xN)` | Row-wise median | Requires all numeric args | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| numeric | `ROUND` | `round(x <, unit>)` | Round to nearest multiple of unit | Unit is not decimal places — see Rule 5 | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| numeric | `INT` | `int(x)` | Truncate toward 0 | Negative numbers round up, not down | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| numeric | `CEIL` | `ceil(x)` | Smallest integer ≥ x | Fuzzed near integers | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| numeric | `FLOOR` | `floor(x)` | Largest integer ≤ x | Fuzzed near integers | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| numeric | `MOD` | `mod(x, y)` | Remainder | Sign follows dividend — see Rule 7 | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| numeric | `LOG` | `log(x)` | Natural log | Not log10 — name confusion from other languages | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| numeric | `EXP` | `exp(x)` | e^x | Overflow at x ≈ 709 | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| numeric | `MAX` | `max(a, b, ...)` | Row-wise max of nonmissing | Different from `PROC SQL MAX(col)` aggregate | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| numeric | `MIN` | `min(a, b, ...)` | Row-wise min of nonmissing | Different from `PROC SQL MIN(col)` aggregate | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| array | `DIM` | `dim(arr <, dim-n>)` | Length of array (or nth dim) | On 2D arrays, omitting n returns first-dim length | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| array | `HBOUND` | `hbound(arr <, n>)` | Upper bound of array index | Nonzero lower-bound arrays common in time-series work | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| array | `LBOUND` | `lbound(arr <, n>)` | Lower bound of array index | Default is 1 unless explicit `array a{0:10}` | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| macro-aware | `%SYSFUNC` | `%sysfunc(func(args) <, fmt>)` | Call DATA-step function from macro context | Inner commas in func args confuse the parser | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| macro-aware | `%SCAN` | `%scan(text, n <, delim>)` | Macro-context SCAN | Same default-delim trap as SCAN (Rule 1) | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| macro-aware | `%SUBSTR` | `%substr(text, pos <, len>)` | Macro-context SUBSTR | No macro-context SUBSTRN equivalent — beware pos ≤ 0 | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |

## Silent Pitfalls

- **SCAN default delimiters include comma and period** — `SCAN('A,B.C', 2)`
  returns `B`, not `B.C`, because comma and period are both default
  delimiters on ASCII. Always pass the third `character-list` argument
  explicitly when the input has any punctuation. See Rule 1.
  Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm

- **SUBSTR sets `_ERROR_=1` on nonpositive position** — the step
  continues and produces output, but `_ERROR_=1` flows into downstream
  error-flag logic and (depending on `ERRORCHECK`) can halt macro
  loops. `SUBSTRN` is the safer substring for defensive code. See
  Rule 2.
  Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm

- **INTNX default alignment is `BEGINNING`** — `intnx('month', dt, 0)`
  is the first of the month, not `dt`. Every `INTNX` call in a claims
  pipeline should carry an explicit alignment argument. See Rule 3.
  Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm

- **SUM vs `+`** — `SUM(of x1-x5)` treats missing as 0; `x1+x2+...` is
  missing if any arg is missing. Mixing the two in nested expressions
  produces surprising shape-changes on row-wise totals. See Rule 4.
  Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm

- **ROUND unit vs decimal places** — `ROUND(x, 2)` rounds to the
  nearest even integer, not 2 decimals. Use `ROUND(x, 0.01)`. See
  Rule 5.
  Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm

- **COMPRESS `'k'` inversion** — without `'k'`, the listed chars are
  **removed**; with `'k'`, they are the **only** chars kept. `COMPRESS(s,
  , 'a')` removes all alphabetic — the opposite of what "compress with
  alpha" sounds like in English. See Rule 6.
  Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm

- **MOD sign-of-dividend** — `MOD(-7, 3) = -1`, not `2`. Code that
  uses `MOD` for hash-bucket assignment on signed keys will produce
  negative bucket indices. See Rule 7.
  Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm

- **CATS / CATT / CATX default length 200** — all three default the
  result variable to 200 bytes when one has not been assigned. Long
  concatenations truncate to 200 silently in DATA steps outside WHERE
  clauses; WHERE-clause and PROC SQL usage truncates even more
  aggressively. Declare `length` explicitly. See Rule 8.
  Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm

## Anti-patterns (STOP signs)

**STOP** when you see any of the following — the code compiles and
produces output, but the output is almost certainly wrong:

- `scan(str, n)` with no delimiter argument and a `str` that can
  contain any punctuation → see Rule 1.
- `substr(str, pos, len)` where `pos` comes from `find()` or
  `index()` without a `> 0` guard → see Rule 2. Use `SUBSTRN`.
- `intnx('month', d, n)` with no fourth argument when you meant
  "same-day n months later" → see Rule 3.
- `a + b + c` across a set of variables that may be missing, when
  what you meant was "total of present values" → see Rule 4. Use
  `SUM(of ...)`.
- `round(x, 2)` intending 2 decimal places → see Rule 5. Use
  `round(x, 0.01)`.
- `compress(str, '0123456789')` intending "keep only digits" → see
  Rule 6. Default is removal; add `'k'` to invert.
- `mod(x, n)` where `x` can be negative and `bucket >= 0` is required
  → see Rule 7.
- `cats(a, b, c)` or `catx('|', a, b, c)` with no `length` statement
  and a long expected result → see Rule 8. Declare `length` first.

## See Also

- [data-step.md](data-step.md) — DATA-step statement-level reference
  (MERGE, BY, RETAIN, `first.`/`last.`, array **declaration**); `LAG`
  queue semantics, `COALESCE`, `CALL MISSING`.
- [macros.md](macros.md) — macro-language authoring, quoting
  functions, `%SYSFUNC` deep dive.
- [proc-sql.md](proc-sql.md) — SQL-context `MAX` / `MIN` / `SUM`
  aggregates (contrast with the row-wise DATA-step versions here) and
  `COALESCE` in SQL joins.
- [base-procs.md](base-procs.md) — `PROC MEANS` / `PROC UNIVARIATE`
  for column-wise descriptive statistics (contrast with the row-wise
  `MEAN` / `MEDIAN` functions here).
- [formats-informats.md](formats-informats.md) — date/time formats
  used with `PUT` after `INTNX` / `MDY` / `TODAY`; ISO-format
  round-trips.
- [SAS Functions and CALL Routines: Reference](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm)
