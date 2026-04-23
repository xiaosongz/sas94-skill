---
title: String cleaning — COMPRESS / TRANWRD / TRANSLATE / STRIP / TRIM / COMPBL
loaded_when: '"COMPRESS", "TRANWRD", "TRANSLATE", "STRIP", "TRIM", "LEFT", "COMPBL", "remove characters", "replace in string", "strip blanks", "keep only digits", "scrub", "clean string".'
---

## Critical Rules

### Rule: `COMPRESS(str, list, 'k')` **keeps** only chars in `list` — the `k` modifier inverts the default "remove" semantics

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

## Quick Ref

| Name | Syntax | Purpose | Common mistake |
|------|--------|---------|----------------|
| `COMPRESS` | `compress(s <, chars <, mod>>)` | Remove listed chars (or keep with `'k'`) | `'k'` modifier inverts meaning — see Rule above |
| `TRANWRD` | `tranwrd(s, old, new)` | Replace all occurrences of `old` with `new` | Case-sensitive; no regex |
| `TRANSLATE` | `translate(s, to, from)` | Char-by-char swap | Argument order is `to, from` — opposite of tr(1) |
| `STRIP` | `strip(s)` | Remove leading and trailing blanks | Not for interior whitespace |
| `TRIM` | `trim(s)` | Remove trailing blanks only | Leading blanks preserved; use STRIP for both sides |
| `LEFT` | `left(s)` | Left-align (move leading blanks to trailing) | Doesn't shorten the string; pair with `TRIM` |
| `COMPBL` | `compbl(s)` | Collapse runs of interior blanks to one | Doesn't trim leading/trailing — wrap with `STRIP` |

## Class modifiers for `COMPRESS`

Compose these with `'k'` to build "keep only class X" one-liners:

- `'a'` — alphabetic
- `'d'` — digits
- `'p'` — punctuation
- `'s'` — whitespace (space, tab, CR, LF, FF, VT)
- `'i'` — case-insensitive (for the `chars` argument)

Examples:

```sas
/* keep only alphanumerics */
clean = compress(raw, , 'kad');

/* remove all whitespace including interior tabs/CRs */
no_ws = compress(raw, , 's');

/* scrub all punctuation */
no_punct = compress(raw, , 'p');
```

## Silent Pitfalls

- **COMPRESS `'k'` inversion** — without `'k'`, the listed chars are
  **removed**; with `'k'`, they are the **only** chars kept. `COMPRESS(s,
  , 'a')` removes all alphabetic — the opposite of what "compress with
  alpha" sounds like in English.

- **TRANWRD is case-sensitive** — `tranwrd(dx, 'diab', 'DM')` misses
  `'Diabetes'`. Either UPCASE both sides first or use a two-step
  `TRANWRD(TRANWRD(str, 'diab', 'DM'), 'Diab', 'DM')`.

- **TRANSLATE argument order is `to, from`** — the inverse of the Unix
  `tr` utility. `translate(s, '_', '-')` swaps hyphens to underscores,
  not the other way around. Easy to get backwards when porting from
  shell scripts.

- **STRIP / TRIM don't touch interior whitespace** — `strip('  a   b  ')`
  returns `'a   b'` (interior triple-space preserved). Use `COMPBL` for
  interior collapse, or `COMPRESS(s, ' ')` to delete all spaces.

- **TRIM alone is almost always wrong in concatenation** — `trim(a) ||
  '-' || trim(b)` preserves leading blanks on `a` and `b`. Use `STRIP`
  or skip the manual trimming and reach for `CATX` (see `concat.md`).

## Anti-patterns

**STOP** when you see any of the following — the code compiles and
produces output, but the output is almost certainly wrong:

- `compress(str, '0123456789')` intending "keep only digits" — see the
  Rule above. Default is removal; add `'k'` to invert.
- `tranwrd(dx, 'diab', 'DM')` on a free-text clinical-notes column
  without first applying `UPCASE` / `LOWCASE` — case-sensitive matcher
  silently misses mixed-case hits.
- `translate(s, '-', '_')` when you meant "turn underscores into
  hyphens" — the argument order is `to, from`, so this does the
  opposite of what it reads.
- `trim(s)` used for "clean up the value" — it only touches trailing
  blanks. Reach for `STRIP` (both sides) or `COMPBL` (interior
  collapse) depending on intent.
