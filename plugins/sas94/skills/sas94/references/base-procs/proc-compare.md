---
title: PROC COMPARE — METHOD=EXACT default, CRITERION semantics
loaded_when: '"PROC COMPARE", "dataset equality", "dataset diff", "METHOD=EXACT", "METHOD=RELATIVE", "METHOD=PERCENT", "CRITERION=", "LISTALL", or "compare base= compare=".'
---

## Critical Rules

### Rule 10 (COMPARE half): `PROC COMPARE` defaults are permissive on metadata — labels/formats/informats ignored unless asked

`PROC COMPARE` defaults depend on `METHOD=`. The default
`METHOD=EXACT` is bit-for-bit strict — no tolerance applied to
numerics, a 1 ULP difference reports. The often-quoted
"permissive 0.00001 tolerance" is `CRITERION=0.00001` — but that
only takes effect when `METHOD=RELATIVE` or `METHOD=PERCENT` is
explicitly requested. The silent gap lies elsewhere: labels,
formats, and informats are ignored in the default equality test
unless asked for. For a fully explicit comparison use
`CRITERION=0 METHOD=EXACT LISTALL` to enumerate every difference
category (value, label, format, length, label, informat, etc.).

```sas
/* CORRECT - strict dataset-equality check, every difference category listed */
proc compare base=work.claims_v1
             compare=work.claims_v2
             method=exact criterion=0 listall;
run;
```

## Quick Ref

| Option | Purpose | Common mistake |
|--------|---------|----------------|
| `base=a compare=b` | Two datasets to diff | Swapping → report labels confusing |
| `method=exact` (default) | Bit-for-bit numeric compare | No tolerance; 1 ULP flagged |
| `method=relative` / `percent` | Tolerance-based compare | Only here does `criterion=` apply |
| `criterion=0.00001` | Tolerance threshold | Does **nothing** under `method=exact` |
| `listall` | Enumerate every diff category | Omitting → label/format diffs hidden |
| `out=ds outnoequal` | Output differences dataset | Forgetting → no programmatic access |

## Anti-patterns (STOP signs)

- `proc compare base=a compare=b;` with default `CRITERION` used as a
  pass/fail gate → within-tolerance differences hidden; label / format
  / informat mismatches silently ignored. Use
  `METHOD=EXACT CRITERION=0 LISTALL`.
