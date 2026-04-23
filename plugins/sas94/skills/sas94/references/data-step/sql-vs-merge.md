---
title: SQL join vs DATA-step MERGE semantics
loaded_when: '"PROC SQL" join, choosing between SQL join and MERGE, Cartesian product, "a.*, b.*", ambiguous column names in a join, full outer join with coalesced keys.'
---

## Critical Rules

### Rule 4: SQL join vs MERGE — different semantics, different failure modes; use explicit `coalesce` in joins (GWU §4)

DATA-step MERGE requires sorted BY variables and right-overwrites
silently; PROC SQL joins do not require sorting, but `a.*, b.*` in the
select list produces ambiguous same-named columns and — on unqualified
`FROM a, b` without a `WHERE` — a silent Cartesian product. Qualify every
shared column and use `COALESCE` to pick a single value explicitly.

```sas
/* CORRECT — qualify each column; coalesce shared payloads explicitly */
proc sql;
  create table members_all as
  select
      a.member_id,
      coalesce(a.paid_amt, b.paid_amt) as paid_amt,
      a.service_dt,
      b.dx_code
  from elig as a
  full join claims as b
    on a.member_id = b.member_id;
quit;
```

```sas
/* WRONG — unqualified select *, comma-join with no WHERE; silent Cartesian */
proc sql;
  create table members_all as
  select a.*, b.*
  from elig as a, claims as b;   /* no ON / no WHERE — every elig row × every claim row */
quit;
```

## Silent Pitfalls

- **Unqualified `select a.*, b.*`** — same-named columns collapse to
  whichever side SQL happens to pick, with no consistent rule across
  SAS versions. Qualify every shared column, alias with `as`, or
  `coalesce(a.x, b.x) as x`.
- **Comma-join without `WHERE`** — a comma-separated FROM list with no
  predicate is a Cartesian product. No warning. Row count explodes
  silently; downstream steps look normal until someone checks totals.
- **`FULL JOIN` without coalescing the key** — the join key itself may
  be NULL on one side; select `coalesce(a.id, b.id) as id` so the
  result-set key column is never missing.

## Anti-patterns (STOP signs)

**STOP** when you see any of the following — the code compiles and
produces output, but the output is almost certainly wrong:

- `select a.*, b.*` in a PROC SQL join where `a` and `b` share column
  names other than the join key → ambiguous; see Rule 4 / GWU §4.
- `from a, b` with no `where` / `on` → silent Cartesian.
- MERGE used where the two inputs are not pre-sorted on the BY
  variables; NOTE-level diagnostic only, easily missed in a long log.

## Related

DATA-step side of the same join-semantics problem: `merge.md`. For
SQL-specific mechanics (GROUP BY remerging, correlated subqueries), see
prose references to PROC SQL.
