---
title: Numeric formats — best / dollar / comma / w.d width rules
loaded_when: '"best.", "dollar.", "comma.", "w.d", "numeric format", "width", "asterisks", "format truncation", "input(str, best", or any numeric display / coercion task.'
---

## Critical Rules

### Rule 7: Format width controls display truncation but NOT stored precision

`format x 5.;` limits the printed width to 5 characters — a
6-digit integer prints as `*****` (the overflow indicator). The
stored 8-byte numeric is unaffected; subsequent PROCs still see
the full value. This is the mirror bug of "I set the format so my
value is wrong" — it isn't wrong, just hidden. Use `best12.` or
a wider `w.d` when unsure; use narrower widths deliberately for
columnar reports.

```sas
/* CORRECT - wide enough for realistic paid amounts */
data costs_display;
  set costs;
  format paid_amt dollar12.2;
run;
```

```sas
/* WRONG - format 6.2 truncates paid_amt = 1234.56 to **** */
data costs_display;
  set costs;
  format paid_amt 6.2;
run;
/* the stored value is still 1234.56 but displays as asterisks */
```

## Canonical Idioms

### `input()` inside a DATA step to coerce a numeric-looking character column

Pipeline handoff bug: a numeric column arrives as character
(`'1234.56'`) because it was read from CSV with default informats.
Convert it inline with `input(str, best.)` rather than a round-trip
through PROC SQL or a rename.

```sas
data costs_num;
  set costs_char;
  paid_num = input(paid_str, best12.);
  format paid_num dollar12.2;
  drop paid_str;
run;
```

## Quick Ref

| Name | Syntax | Purpose | Common mistake |
|------|--------|---------|----------------|
| `best.` | `x = input(str, best12.);` | Auto-pick numeric width | Misreading commas / parens as non-numeric |
| `dollar.` | `format paid dollar12.2;` | Currency display with `$` and commas | Too-narrow width → asterisks (Rule 7) |
| `comma.` | `format n comma10.;` | Thousands separators | Counting the commas against the width budget |
| `w.d` | `format x 8.2;` | Fixed-width numeric with `d` decimals | Narrow width truncates to `*` (Rule 7) |

## Width-counting cheat sheet

The width in `dollar12.2` or `comma10.` INCLUDES every character
that appears in the output — the `$`, the commas, the decimal
point, a minus sign, and the decimal digits. Budget accordingly:

- `1234567.89` with `dollar12.2` → `'$1,234,567.89'` (13 chars, too
  narrow → asterisks). Use `dollar14.2`.
- A negative value needs one extra position for the sign: `-1234.56`
  with `dollar9.2` → `'-1,234.56'` (exactly 9); with `dollar8.2`
  it overflows.
- `best.` auto-negotiates width but still truncates at the declared
  `w` — `best6.` on `1234567` prints in scientific notation or
  asterisks.

## Silent Pitfalls

- **Format width narrower than the value** — `format x 5.;`
  truncates display to `*****`; the stored value is still full
  precision. See Rule 7.
- **Comma / dollar width underestimate** — the `$`, commas, minus
  sign, and decimal point all consume positions; `dollar10.2` on
  `1234567.89` overflows.
- **`best.` in PROC PRINT output** — `best12.` is the default and
  uses scientific notation past a threshold; set an explicit
  `comma` / `dollar` / `w.d` for reports.
- **`input(num_var, best.)`** — direction inversion; `input()`
  wants a string. See `put-vs-input.md` Rule 1.

## Anti-patterns

**STOP** when you see any of the following:

- `format paid_amt 6.2;` on dollar-scale data → display truncates
  to asterisks. See Rule 7.
- `format revenue dollar10.2;` where max value is 9-digit →
  overflow; widen to `dollar14.2`.
- `input(num_var, best.)` on an already-numeric column → direction
  inversion; see `put-vs-input.md` Rule 1.

Procs that honor attached numeric formats for display grouping:
see `../base-procs/proc-freq.md` and `../base-procs/proc-report.md`.
