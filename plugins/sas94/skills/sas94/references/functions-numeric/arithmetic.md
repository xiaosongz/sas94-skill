---
title: Scalar arithmetic functions — ROUND, INT, CEIL, FLOOR, MOD, ABS, LOG, EXP
loaded_when: '"ROUND", "ROUND unit", "INT function", "CEIL", "FLOOR", "MOD", "modulo", "ABS", "SIGN", "LOG function", "EXP", or any scalar numeric / rounding / precision lookup.'
---

## Critical Rules

### Rule 1: `ROUND(x, unit)` rounds to the nearest **multiple of unit**, not to a number of decimal places

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

### Rule 2: `MOD(-7, 3)` returns `-1`, not `2` — SAS uses sign-of-dividend, not the mathematical modulo

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

## Canonical Idiom: PMPM currency rounding to two decimals with `ROUND(x, 0.01)`

Purpose: round per-member-per-month cost ratios to two decimal places
for reporting. The rounding **unit** is `0.01`, not `2` — see Rule 1.
Use `ROUND` (not `PUT(x, best12.2)`) when the downstream step arithmetic
needs the truncated value as a number, not a formatted string.

```sas
data pmpm_summary; set pmpm_raw;
  pmpm = round(total_paid / member_months, 0.01);   /* unit = 0.01 */
run;
```

## Canonical Idiom: Nonnegative-bucket hash with `ABS` guard around `MOD`

Purpose: assign rows to a nonnegative bucket index for parallelized
or sharded processing. Because SAS's `MOD` takes the sign of the
dividend (Rule 2), wrap the key with `ABS()` before the modulo call —
otherwise negative keys produce negative bucket indices that break
downstream `by bucket` grouping.

```sas
data claims_bucketed; set claims;
  bucket = mod(abs(acct_hash), 16);   /* always in [0, 16) */
run;
```

## Quick Ref

| Name | Syntax | Purpose | Common mistake |
|------|--------|---------|----------------|
| `ROUND` | `round(x <, unit>)` | Round to nearest multiple of unit | Unit is not decimal places — see Rule 1 |
| `INT` | `int(x)` | Truncate toward 0 | Negative numbers round up, not down |
| `CEIL` | `ceil(x)` | Smallest integer ≥ x | Fuzzed near integers |
| `FLOOR` | `floor(x)` | Largest integer ≤ x | Fuzzed near integers |
| `ABS` | `abs(x)` | Absolute value | Undefined on missing — returns missing |
| `MOD` | `mod(x, y)` | Remainder | Sign follows dividend — see Rule 2 |
| `LOG` | `log(x)` | Natural log | Not log10 — name confusion from other languages |
| `EXP` | `exp(x)` | e^x | Overflow at x ≈ 709 |

## Silent Pitfalls

- **ROUND unit vs decimal places** — `ROUND(x, 2)` rounds to the
  nearest even integer, not 2 decimals. Use `ROUND(x, 0.01)`. See
  Rule 1.

- **MOD sign-of-dividend** — `MOD(-7, 3) = -1`, not `2`. Code that
  uses `MOD` for hash-bucket assignment on signed keys will produce
  negative bucket indices. See Rule 2.

- **`INT` vs `FLOOR` on negatives** — `INT(-1.5) = -1` (truncate toward
  zero); `FLOOR(-1.5) = -2` (toward negative infinity). The two agree
  on nonnegative input but diverge on negatives.

- **`LOG` is natural log** — SAS's `LOG(x)` is ln; `LOG10(x)` is base-10.
  R and Python users reach for `LOG` expecting log10 and get silent
  scale errors.

## Anti-patterns (STOP signs)

**STOP** when you see any of the following — the code compiles and
produces output, but the output is almost certainly wrong:

- `round(x, 2)` intending 2 decimal places → see Rule 1. Use
  `round(x, 0.01)`.
- `mod(x, n)` where `x` can be negative and `bucket >= 0` is required
  → see Rule 2. Wrap with `abs()` or rewrite.
- `log(x)` intending log-base-10 → use `log10(x)`. `log(x)` is ln.
- For `%SYSEVALF` macro-context floating-point arithmetic (contrast
  with integer-only `%EVAL`), see `../macros/sysfunc-and-eval.md`.
