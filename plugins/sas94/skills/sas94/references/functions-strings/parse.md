---
title: String parsing — SCAN / SUBSTR / SUBSTRN / FIND / INDEX / COUNTW
loaded_when: '"SCAN", "%scan", "SUBSTR", "%substr", "SUBSTRN", "FIND", "INDEX", "COUNTW", "delimiter", "tokenize", "parse string", "extract word", "extract substring", "ICD prefix".'
---

## Critical Rules

### Rule 1: `SCAN(str, n)` without an explicit delimiter uses SAS's default delimiter set — which includes comma, period, and parentheses

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

## Canonical Idioms

### Idiom: ICD-10 code prefix match with `SUBSTRN`

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

### Idiom: `%SCAN` from macro context with a literal-space delimiter

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

## Quick Ref

| Name | Syntax | Purpose | Common mistake |
|------|--------|---------|----------------|
| `SCAN` | `scan(s, n <, delim <, mod>>)` | Extract nth word | Omitting delim uses default set — see Rule 1 |
| `SUBSTR` | `substr(s, pos <, len>)` | Extract fixed-position substring | Nonpositive pos sets `_ERROR_=1` — see Rule 2 |
| `SUBSTRN` | `substrn(s, pos <, len>)` | Safe substring — returns empty on bad pos | Silently empty when you expected content |
| `INDEX` | `index(s, sub)` | Position of first `sub`; 0 if absent | Case-sensitive; no wildcards |
| `FIND` | `find(s, sub <, mods <, start>>)` | Positional search with `'i'` case-insens mod | Forgetting `'i'` and missing mixed-case matches |
| `COUNTW` | `countw(s <, delim>)` | Count words | Same default-delim trap as SCAN |
| `%SCAN` | `%scan(text, n <, delim>)` | Macro-context SCAN | Same default-delim trap as SCAN (Rule 1) |
| `%SUBSTR` | `%substr(text, pos <, len>)` | Macro-context SUBSTR | No macro-context SUBSTRN equivalent — beware pos ≤ 0 |

## Silent Pitfalls

- **SCAN default delimiters include comma and period** — `SCAN('A,B.C', 2)`
  returns `B`, not `B.C`. Always pass the third `character-list`
  argument explicitly when the input has any punctuation. See Rule 1.

- **SUBSTR sets `_ERROR_=1` on nonpositive position** — the step
  continues and produces output, but `_ERROR_=1` flows into downstream
  error-flag logic and (depending on `ERRORCHECK`) can halt macro
  loops. `SUBSTRN` is the safer substring for defensive code. See
  Rule 2.

- **FIND without `'i'` modifier is case-sensitive** — `find(dx, 'diab')`
  misses `'Diabetes'`. Pass `'i'` when the source column is free-text
  clinical notes or anything hand-entered.

- **COUNTW inherits the SCAN default-delim trap** — a naked `countw(str)`
  counts period- and comma-separated tokens as distinct words. Pass the
  delimiter argument.

## Anti-patterns

**STOP** when you see any of the following — the code compiles and
produces output, but the output is almost certainly wrong:

- `scan(str, n)` with no delimiter argument and a `str` that can
  contain any punctuation — see Rule 1.
- `substr(str, pos, len)` where `pos` comes from `find()` or
  `index()` without a `> 0` guard — see Rule 2. Use `SUBSTRN`.
- `%substr(&val, n)` where `&val` can be empty — errors hard in macro
  context; guard with `%if %length(&val) >= n`.
