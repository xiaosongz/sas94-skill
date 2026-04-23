---
title: Case folding and string comparison — UPCASE / LOWCASE / PROPCASE / COMPARE
loaded_when: '"UPCASE", "LOWCASE", "PROPCASE", "COMPARE", "case-insensitive", "title case", "uppercase", "lowercase", "trailing blanks comparison", "string equality".'
---

String equality in SAS ignores trailing blanks by default, and the
case-folding functions are strictly ASCII — two facts that trip up
anyone porting from locale-aware languages (Python `str.casefold`,
R `tolower`) or from systems where `=` is byte-exact.

## Critical behaviors

- SAS `=` comparison on character columns **ignores trailing blanks** on
  both sides — `'A  ' = 'A'` is true. For length-sensitive equality use
  `COMPARE(a, b, 'l')` or compare lengths first.
- `UPCASE` / `LOWCASE` fold only ASCII `A-Z` / `a-z`. Accented letters,
  eszett, dotless-i, and non-Latin scripts pass through unchanged. Not
  safe for internationalized name fields.
- `PROPCASE(str)` with no second argument splits on the default
  delimiter set: **space, forward slash, hyphen, hyphen-minus, tab,
  backslash, line feed, carriage return, period**. `PROPCASE('MCDONALD')`
  returns `Mcdonald`, not `McDonald` — the `Mc`/`Mac` case is lost.

```sas
/* CORRECT - case-insensitive match via uniform UPCASE */
if upcase(dx_notes) =: 'DIAB' then flag_dm = 1;
```

```sas
/* CORRECT - length-sensitive equality test */
if compare(a, b, 'l') = 0 then matched = 1;
```

```sas
/* WRONG - raw equality ignores trailing blanks, produces false positives */
if member_id = trimmed_id then ...;
/* 'A12   ' = 'A12' is TRUE even though lengths differ */
```

## Quick Ref

| Name | Syntax | Purpose | Common mistake |
|------|--------|---------|----------------|
| `UPCASE` | `upcase(s)` | ASCII uppercase | Not locale-aware |
| `LOWCASE` | `lowcase(s)` | ASCII lowercase | Not locale-aware |
| `PROPCASE` | `propcase(s <, delims>)` | Title-case every word | Default delims include space, hyphen, tab |
| `COMPARE` | `compare(a, b <, mods>)` | 0 if equal; char-pos of first diff otherwise | Bare form ignores trailing blanks like `=` |

## `COMPARE` modifiers

Compose these in the third argument to control equality semantics:

- `'i'` — case-insensitive
- `'l'` — length-sensitive (do not ignore trailing blanks)
- `'n'` — ignore quotes
- `':'` (colon in the mods string) — match only the length of the
  shorter string, i.e. `a =: b`

`compare(a, b, 'il')` gives case-insensitive, length-sensitive
equality — the most common "defensive string match" combination.

## Silent Pitfalls

- **`=` ignores trailing blanks** — a deliberate SAS design choice that
  surprises everyone. `'A12 '` equals `'A12'` in a WHERE clause and in
  an `IF`. For exact-length equality, use `COMPARE(a, b, 'l') = 0` or
  test `length(a) = length(b)` first.

- **`UPCASE` / `LOWCASE` are not locale-aware** — they fold only
  ASCII `A-Z` / `a-z`. Do not rely on them for case-insensitive match
  of names containing accented characters, umlauts, cedillas, etc.
  Downcast upstream or use a dedicated locale-aware preprocessor.

- **`PROPCASE` default delimiters split on period and slash** —
  `PROPCASE('smith.john')` returns `Smith.John`, and
  `PROPCASE('a/b/c')` returns `A/B/C`. If the column contains URLs or
  dotted identifiers, pass an explicit delimiter set as the second
  argument.

- **The `=:` operator compares only the shorter length** — useful for
  prefix matching (`if dx =: 'I10'`), but silently makes `'I10' =: 'I1'`
  true. Pair with an explicit `length` check when the intent is
  "exactly three characters starting with I10".

## Anti-patterns

**STOP** when you see any of the following — the code compiles and
produces output, but the output is almost certainly wrong:

- `if a = b` on character columns where trailing-blank equality would
  be a false positive (e.g. hash-key lookups, dedup checks). Reach for
  `COMPARE(a, b, 'l') = 0`.
- `upcase(name) = 'MCDONALD'` expecting international name matching —
  non-ASCII letters pass through unchanged. Normalize upstream.
- `propcase(name)` on a `firstname.lastname`-format username column —
  the period is a default delimiter, so both halves get capitalized
  independently and the dot is preserved. Strip or replace the dot
  first.
