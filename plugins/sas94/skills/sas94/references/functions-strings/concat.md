---
title: String concatenation — CATS / CATT / CATX / CAT / `||`
loaded_when: '"CATS", "CATT", "CATX", "CAT", "concatenate", "concat", "composite key", "dedup key", "||" string-operator, "trailing blanks" when joining.'
---

## Critical Rules

### Rule: `CATS`, `CATT`, and `CATX` differ in which blanks they strip — pick deliberately, don't reach for whichever you remember

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

### Idiom: `CATX`-assembled composite key for dedup or merge

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

## Quick Ref

| Name | Syntax | Purpose | Common mistake |
|------|--------|---------|----------------|
| `CATS` | `cats(a, b, ...)` | Concat, strip all blanks, no separator | Collapses values without separator — see Rule above |
| `CATT` | `catt(a, b, ...)` | Concat, strip trailing only | Leading blanks preserved — rarely what's wanted |
| `CATX` | `catx(sep, a, b, ...)` | Concat with separator, strip blanks | Default result length 200 — truncates long keys |

`CAT(a, b, ...)` (no strip) and `||` operator preserve trailing blanks
from fixed-width character columns — almost always a bug in DATA-step
joins. Use `CATS` / `CATT` / `CATX` instead unless you explicitly need
the padded form (e.g., fixed-width export files).

## Silent Pitfalls

- **CATS / CATT / CATX default length 200** — all three default the
  result variable to 200 bytes when one has not been assigned. Long
  concatenations truncate to 200 silently in DATA steps outside WHERE
  clauses; WHERE-clause and PROC SQL usage truncates even more
  aggressively. Declare `length` explicitly.

- **Numeric-operand coercion writes a NOTE** — passing a numeric column
  to `CATS` / `CATX` triggers an automatic `PUT(x, BEST12.)` conversion
  and writes a `NOTE: Numeric values have been converted to character`
  message to the log. Wrap numerics in an explicit `PUT(col, fmt.)` to
  silence the note and control the format — crucial for dates (default
  `BEST12.` produces the SAS internal day count, not `yymmdd10.`).

- **`||` preserves trailing blanks from fixed-width char columns** —
  `name_first || ' ' || name_last` on `$20`-wide columns produces
  `"John                 Smith               "`, not `"John Smith"`.
  Use `CATX(' ', name_first, name_last)` instead.

## Anti-patterns

**STOP** when you see any of the following — the code compiles and
produces output, but the output is almost certainly wrong:

- `cats(a, b, c)` or `catx('|', a, b, c)` with no `length` statement
  and a long expected result — declare `length` first.
- `a || '-' || b` on fixed-width character columns when the intent is
  a compact key — reach for `CATX('-', a, b)`.
- `cats(member_id, service_dt)` with a numeric `service_dt` — the log
  warns and the resulting key uses the internal day count. Wrap
  `put(service_dt, yymmdd10.)` explicitly.
