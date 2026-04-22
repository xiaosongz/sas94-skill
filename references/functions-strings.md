---
title: SAS string function reference
scope: String-manipulation function cheatsheet — SCAN, SUBSTR/SUBSTRN, CATS/CATT/CATX, COMPRESS, COMPBL, INDEX/FIND, TRANWRD, TRANSLATE, PROPCASE/UPCASE/LOWCASE, STRIP/TRIM, LENGTH/LENGTHN. Focused on default-delimiter traps, position-underflow errors, and blank-stripping semantics that produce silent bugs in claims-data text parsing.
loaded_when: '"SCAN", "SUBSTR", "SUBSTRN", "CATX", "CATS", "CATT", "COMPRESS", "TRANWRD", "INDEX", "FIND", "PROPCASE", "UPCASE", "LOWCASE", "STRIP", "TRIM", "LENGTH", "%scan", "%substr", or any string function lookup.'
last_reviewed: 2026-04-22
reviewer: xiaosongz
---

## Overview

String-manipulation functions are where default arguments bite
hardest. `SCAN(text, 3)` silently breaks when the text contains
comma, period, or parentheses — all default delimiters. `SUBSTR(str,
pos, len)` with nonpositive `pos` sets `_ERROR_=1`; `SUBSTRN` returns
empty instead. `COMPRESS(str, list, 'k')` **keeps** the listed chars;
without `'k'` it **removes** them. This file covers word extraction,
substring, concatenation, character-class scrubbing, search,
replacement, case folding, and trimming. Every rule and idiom cites
the `SAS Functions and CALL Routines: Reference` docset
(`lefunctionsref`).

For date and numeric functions see `functions-dates.md` and
`functions-numeric.md`. For macro-context quoting functions (`%str`,
`%bquote`, `%nrstr`) see `macros.md`.

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

### Rule 3: `COMPRESS(str, list, 'k')` **keeps** only chars in `list` — the `k` modifier inverts the default "remove" semantics

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

### Rule 4: `CATS`, `CATT`, and `CATX` differ in which blanks they strip — pick deliberately, don't reach for whichever you remember

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

### Idiom: `%SCAN` from macro context with a literal-space delimiter

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm

Purpose: pull the first token out of a space-delimited macro variable
from inside macro-context code — for example, peeling the first
element off a `&varlist`. The macro processor sees the comma in
`scan(&list, 1, ' ')` as an argument separator, so the literal delimiter
must be masked with `%str( )` or the call must route through
`%sysfunc(scan(...))` with appropriate quoting. Same default-delim
trap as the DATA-step SCAN (Rule 1): never omit the delimiter
argument when the text could contain punctuation.

```sas
/* SCAN from macro context - inner literal delimiter needs protection */
%let tag = %sysfunc(scan(&list, 1, %str( )));
```

## Function / Statement Quick Ref

| Name | Syntax | Purpose | Common mistake | Doc URL |
|------|--------|---------|----------------|---------|
| `SCAN` | `scan(s, n <, delim <, mod>>)` | Extract nth word | Omitting delim uses default set — see Rule 1 | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| `SUBSTR` | `substr(s, pos <, len>)` | Extract fixed-position substring | Nonpositive pos sets `_ERROR_=1` — see Rule 2 | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| `SUBSTRN` | `substrn(s, pos <, len>)` | Safe substring — returns empty on bad pos | Silently empty when you expected content | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| `CATS` | `cats(a, b, ...)` | Concat, strip all blanks, no separator | Collapses values without separator — see Rule 4 | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| `CATT` | `catt(a, b, ...)` | Concat, strip trailing only | Leading blanks preserved — rarely what's wanted | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| `CATX` | `catx(sep, a, b, ...)` | Concat with separator, strip blanks | Default result length 200 — truncates long keys | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| `TRANWRD` | `tranwrd(s, old, new)` | Replace all occurrences of `old` with `new` | Case-sensitive; no regex | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| `COMPRESS` | `compress(s <, chars <, mod>>)` | Remove listed chars (or keep with `'k'`) | `'k'` modifier inverts meaning — see Rule 3 | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| `INDEX` | `index(s, sub)` | Position of first `sub`; 0 if absent | Case-sensitive; no wildcards | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| `FIND` | `find(s, sub <, mods <, start>>)` | Positional search with `'i'` case-insens mod | Forgetting `'i'` and missing mixed-case matches | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| `TRANSLATE` | `translate(s, to, from)` | Char-by-char swap | Argument order is `to, from` — opposite of tr(1) | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| `PROPCASE` | `propcase(s <, delims>)` | Title-case every word | Default delims include space, hyphen, tab | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| `UPCASE` | `upcase(s)` | ASCII uppercase | Not locale-aware | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| `LOWCASE` | `lowcase(s)` | ASCII lowercase | Not locale-aware | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| `STRIP` | `strip(s)` | Remove leading and trailing blanks | Not for interior whitespace | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| `TRIM` | `trim(s)` | Remove trailing blanks only | Leading blanks preserved; use STRIP for both sides | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| `%SCAN` | `%scan(text, n <, delim>)` | Macro-context SCAN | Same default-delim trap as SCAN (Rule 1) | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| `%SUBSTR` | `%substr(text, pos <, len>)` | Macro-context SUBSTR | No macro-context SUBSTRN equivalent — beware pos ≤ 0 | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |

## Silent Pitfalls

All pitfalls below share the same source:
https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm

- **SCAN default delimiters include comma and period** — `SCAN('A,B.C', 2)`
  returns `B`, not `B.C`. Always pass the third `character-list`
  argument explicitly when the input has any punctuation. See Rule 1.

- **SUBSTR sets `_ERROR_=1` on nonpositive position** — the step
  continues and produces output, but `_ERROR_=1` flows into downstream
  error-flag logic and (depending on `ERRORCHECK`) can halt macro
  loops. `SUBSTRN` is the safer substring for defensive code. See
  Rule 2.

- **COMPRESS `'k'` inversion** — without `'k'`, the listed chars are
  **removed**; with `'k'`, they are the **only** chars kept. `COMPRESS(s,
  , 'a')` removes all alphabetic — the opposite of what "compress with
  alpha" sounds like in English. See Rule 3.

- **CATS / CATT / CATX default length 200** — all three default the
  result variable to 200 bytes when one has not been assigned. Long
  concatenations truncate to 200 silently in DATA steps outside WHERE
  clauses; WHERE-clause and PROC SQL usage truncates even more
  aggressively. Declare `length` explicitly. See Rule 4.

## Anti-patterns (STOP signs)

**STOP** when you see any of the following — the code compiles and
produces output, but the output is almost certainly wrong:

- `scan(str, n)` with no delimiter argument and a `str` that can
  contain any punctuation → see Rule 1.
- `substr(str, pos, len)` where `pos` comes from `find()` or
  `index()` without a `> 0` guard → see Rule 2. Use `SUBSTRN`.
- `compress(str, '0123456789')` intending "keep only digits" → see
  Rule 3. Default is removal; add `'k'` to invert.
- `cats(a, b, c)` or `catx('|', a, b, c)` with no `length` statement
  and a long expected result → see Rule 4. Declare `length` first.

## See Also

- [functions-dates.md](functions-dates.md) — date/time functions
  (INTNX, INTCK, TODAY, MDY, DATEPART) that feed date-string
  parsing / formatting idioms here.
- [functions-numeric.md](functions-numeric.md) — numeric and array
  functions (SUM, ROUND, MOD, DIM).
- [formats-informats.md](formats-informats.md) — `INPUT()` / `PUT()`
  string-to-variable and variable-to-string conversions that wrap
  around the SCAN / SUBSTR family.
- [data-step.md](data-step.md) — DATA-step statement-level reference
  (LENGTH / ATTRIB for explicit string widths).
- [macros.md](macros.md) — macro-quoting functions (`%str`, `%bquote`,
  `%nrstr`) around `%SCAN` / `%SUBSTR`.
- [SAS Functions and CALL Routines: Reference](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm)
