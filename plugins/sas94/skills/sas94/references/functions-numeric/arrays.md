---
title: Array inspection functions — DIM, HBOUND, LBOUND
loaded_when: '"DIM function", "HBOUND", "LBOUND", "array index", "iterate array", "array bounds", "do i = 1 to dim", or any array-shape / array-iteration lookup.'
---

## Critical Rules

### Rule 1: `DIM(arr)` returns the number of elements; on multi-dim arrays omitting the dim-index returns the **first** dimension's length

`DIM(arr)` on a 1-D array is the element count. On a 2-D array
`array a{3, 4}`, `DIM(a)` returns `3` (first dim only); use
`DIM(a, 2)` for the second dim. Loops that iterate
`do i = 1 to dim(a)` silently truncate when the array is 2-D and
`a` was flattened downstream.

```sas
/* CORRECT - iterate every element of a 1-D array without hard-coding bounds */
data _null_; set claims;
  array paid{*} paid_ip paid_op paid_rx;
  do i = 1 to dim(paid);
    paid[i] = max(paid[i], 0);
  end;
run;
```

```sas
/* WRONG - hard-coded upper bound drifts when array membership changes */
data _null_; set claims;
  array paid{*} paid_ip paid_op paid_rx;
  do i = 1 to 3;                              /* breaks when paid_dme added */
    paid[i] = max(paid[i], 0);
  end;
run;
```

### Rule 2: `LBOUND` defaults to `1` — use it (not a hard-coded `1`) when the array was declared with an explicit lower bound like `array a{0:10}`

Time-series / zero-offset arrays declared `array lag{0:12}` have
`LBOUND(lag) = 0`, not 1. Iterating `do i = 1 to hbound(lag)` skips
element `lag{0}` silently. Use `do i = lbound(lag) to hbound(lag)`
whenever the array declaration is not colocated with the loop.

```sas
/* CORRECT - bounds-safe iteration over an explicit-lower-bound array */
data _null_; set rates;
  array lag{0:12} lag0-lag12;
  do i = lbound(lag) to hbound(lag);
    lag[i] = coalesce(lag[i], 0);
  end;
run;
```

```sas
/* WRONG - skips lag{0} because hard-coded 1 ignores the declared lower bound */
data _null_; set rates;
  array lag{0:12} lag0-lag12;
  do i = 1 to hbound(lag);
    lag[i] = coalesce(lag[i], 0);
  end;
run;
```

## Canonical Idiom: Bounds-safe array iteration

Purpose: walk every element of an array without assuming either the
lower bound (may not be 1) or the upper bound (may change as variables
are added or removed from the array declaration). Pair `LBOUND` with
`HBOUND`, or — when the array is known to be 1-D with default lower
bound — just use `do i = 1 to dim(arr)`.

```sas
data flagged; set claims;
  array dx{*} dx1-dx25;
  do i = lbound(dx) to hbound(dx);
    if dx[i] in ('E119', 'E1165') then diabetic = 1;
  end;
run;
```

## Quick Ref

| Name | Syntax | Purpose | Common mistake |
|------|--------|---------|----------------|
| `DIM` | `dim(arr <, dim-n>)` | Length of array (or nth dim) | On 2D arrays, omitting n returns first-dim length |
| `HBOUND` | `hbound(arr <, n>)` | Upper bound of array index | Nonzero lower-bound arrays common in time-series work |
| `LBOUND` | `lbound(arr <, n>)` | Lower bound of array index | Default is 1 unless explicit `array a{0:10}` |

## Silent Pitfalls

- **`DIM` on multi-dim arrays** — `DIM(a)` without a dim-index returns
  only the first dimension's length. On `array a{3, 4}` the full
  element count is `DIM(a, 1) * DIM(a, 2) = 12`, not `DIM(a) = 3`.

- **Hard-coded `1` as lower bound** — safe until someone redeclares the
  array as `array lag{0:N}`. Then the first iteration silently skips
  element 0. Always pair `LBOUND` with `HBOUND` for non-colocated
  declarations.

- **Array name collides with numeric variable name** — `array paid{*}
  paid_ip paid_op` inside a DATA step that also has a scalar `paid`
  column resolves to the scalar, not the array, in some expressions.
  Pick a distinct array name (`paid_arr`) to avoid PDV shadowing. See
  `../data-step/retain-pdv.md` for PDV slot semantics.

## Anti-patterns (STOP signs)

**STOP** when you see any of the following — the code compiles and
produces output, but the output is almost certainly wrong:

- `do i = 1 to N` with a hard-coded `N` where `N` must be updated by
  hand whenever the array membership changes → use `do i = 1 to
  dim(arr)` or `do i = lbound(arr) to hbound(arr)`.
- `do i = 1 to hbound(arr)` when the array was declared with an
  explicit non-1 lower bound → see Rule 2. Use `lbound(arr)`.
- `dim(a)` on a 2-D array expecting total element count → see Rule 1.
  Multiply `dim(a, 1) * dim(a, 2)` or iterate nested loops.
