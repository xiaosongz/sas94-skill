---
title: DATA-step MERGE silent overwrite
loaded_when: '"MERGE", "BY processing", BY-group DATA-step join, two datasets sharing a payload column name, choosing between left/right payload values.'
---

## Critical Rules

### Rule 1: MERGE silently overwrites same-named columns — rename on input, then coalesce (GWU §2)

`MERGE a b; BY id;` silently lets `b.var` overwrite `a.var` whenever both
sides carry the same variable name with different values. The SAS log
issues no diagnostic. Rename each side's payload columns on input, then
`coalesce` explicitly in the body of the step.

```sas
/* CORRECT — rename on the way in, then coalesce explicitly */
data members_all;
  merge elig(rename=(paid_amt=paid_amt_elig))
        claims(rename=(paid_amt=paid_amt_clm));
  by member_id;
  paid_amt = coalesce(paid_amt_clm, paid_amt_elig);
run;
```

```sas
/* WRONG — claims.paid_amt silently overwrites elig.paid_amt on shared member_id */
data members_all;
  merge elig claims;
  by member_id;
run;
```

## Silent Pitfalls

- **MERGE overwrite** — same-named variable on both sides silently takes
  the right-side value. Rename payloads on input, then `coalesce`
  explicitly. No log diagnostic is emitted. If BY-group sortedness is
  wrong, a separate NOTE fires, but same-name overwrite never does.
- **Dropped BY variable downstream** — `drop` a BY variable on output and
  every subsequent merge against this dataset silently fails its join.

## Anti-patterns (STOP signs)

**STOP** when you see any of the following — the code compiles and
produces output, but the output is almost certainly wrong:

- `merge a b; by id; run;` with shared payload column names → see Rule 1 / GWU §2.
- Omitting `by` for a MERGE-alternative interleave — SET alone with
  multiple datasets does not align on a key; use `merge ... ; by key;`.

## Related

SQL-join counterpart (same ambiguity, different failure mode): `sql-vs-merge.md`. Alternative for static lookups: hash tables (separate topic).
