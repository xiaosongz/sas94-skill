---
title: LAG queue vs conditional call
loaded_when: '"LAG", previous-row value, row-to-row delta, first./last. gating of a lagged value, time-series diff inside DATA step.'
---

## Critical Rules

### Rule 2: LAG is queue-based — call unconditionally, then gate usage (GWU §1)

`LAG(x)` returns the value from the previous *CALL* to `LAG`, not the
previous *observation*. Placing `LAG` inside a conditional advances its
queue only on matching rows, so the lagged value ends up coming from an
arbitrary earlier row rather than the immediately preceding one. Always
call `LAG` unconditionally, then gate how the result is used.

```sas
/* CORRECT — always advance the lag queue; gate usage afterwards */
data claims_lagged;
  set claims;
  by member_id service_dt;
  prev_paid = lag(paid_amt);                 /* unconditional queue advance */
  if not first.member_id then paid_delta = paid_amt - prev_paid;
run;
```

```sas
/* WRONG — prev_paid queue advances only on non-first rows; lag is misaligned */
data claims_lagged;
  set claims;
  by member_id service_dt;
  if not first.member_id then prev_paid = lag(paid_amt);
run;
```

## Silent Pitfalls

- **LAG inside IF** — `LAG` advances its queue only when called; a
  conditional call misaligns the lag value. Pull the `lag(...)` call
  outside the `if`, then gate the *use* of `prev_*` with the condition.
- **LAGn depth mismatch** — `lag2(x)` needs two previous calls; mixing
  `lag` and `lag2` inside conditionals silently produces empty or stale
  queue slots.
- **LAG across BY groups** — the queue does not reset at a new BY-group
  boundary. Guard with `if first.group then prev = .;` when a fresh
  within-group lag is needed.

## Anti-patterns (STOP signs)

**STOP** when you see any of the following — the code compiles and
produces output, but the output is almost certainly wrong:

- `if cond then lagx = lag(x);` → see Rule 2 / GWU §1.
- `lag(expression)` where the expression is a derived column assigned
  earlier in the same step; the queue loads the *current* row's derived
  value, not the previous row's raw input.

## Related

Carry-forward without a queue (accumulator style): see `retain-pdv.md`. BY-group boundary semantics also relevant to MERGE: see `merge.md`.
