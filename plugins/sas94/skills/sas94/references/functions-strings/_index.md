---
title: String functions — routing index
loaded_when: '"string function", "SCAN", "SUBSTR", "SUBSTRN", "CATX", "CATS", "CATT", "COMPRESS", "TRANWRD", "INDEX", "FIND", "PROPCASE", "UPCASE", "LOWCASE", "STRIP", "TRIM", "%scan", "%substr", or generic string-manipulation lookup.'
---

String-manipulation functions are where default arguments bite hardest.
Route to the atom that matches the function cluster in play. For date/time
and numeric functions, see the sibling `functions-dates.md` and
`functions-numeric.md` files (being split in parallel — use prose lookup).

## Routing table

| Atom | Load when the task involves |
|------|-----------------------------|
| [concat.md](concat.md) | `CATS`, `CATT`, `CATX`, `CAT`, `\|\|` concatenation, trailing-blanks traps, numeric-operand coercion, composite-key assembly |
| [parse.md](parse.md) | `SCAN` (delimiter parsing), `SUBSTR` / `SUBSTRN` (positional extract), `FIND`, `INDEX`, `COUNTW`, ICD-prefix extraction |
| [clean.md](clean.md) | `COMPRESS` (char-class removal or keep-only with `'k'`), `TRANWRD` (literal replace), `TRANSLATE` (char-by-char swap), `STRIP` / `TRIM` / `LEFT`, `COMPBL` |
| [case-and-compare.md](case-and-compare.md) | `UPCASE` / `LOWCASE` / `PROPCASE`, `=` comparison with trailing-blank semantics, `COMPARE` function, case-insensitive matching |

## One-line summaries

- **concat.md** — `CATS` strips all blanks no sep; `CATT` trailing only no sep;
  `CATX(sep, ...)` strips blanks and inserts sep, skipping blank-only args.
  Default result length is 200 — declare `length` for long keys.
- **parse.md** — `SCAN(str, n)` without delim uses the default set (comma,
  period, paren, slash, pipe, etc.) — always pass delim explicitly. `SUBSTR`
  sets `_ERROR_=1` on nonpositive position; `SUBSTRN` returns empty —
  prefer `SUBSTRN` when position comes from `FIND` / arithmetic.
- **clean.md** — `COMPRESS(str, list)` **removes** listed chars;
  `COMPRESS(str, list, 'k')` **keeps** only listed chars. Class modifiers
  (`a` alpha, `d` digit, `p` punct, `s` space) compose with `k`.
- **case-and-compare.md** — `UPCASE` / `LOWCASE` are ASCII-only (not
  locale-aware); `PROPCASE` default delimiters include space, hyphen, tab.
  SAS `=` comparison ignores trailing blanks — use `COMPARE` with `'l'`
  modifier for length-sensitive equality.

## Macro-context equivalents

`%SCAN` and `%SUBSTR` are covered inline in [parse.md](parse.md) — both
share the DATA-step defaults-trap. There is no `%SUBSTRN`; guard position
with `%eval` before calling `%SUBSTR`. For macro quoting around string
literals passed to these calls, see `../macros/scope-and-quoting.md`.
