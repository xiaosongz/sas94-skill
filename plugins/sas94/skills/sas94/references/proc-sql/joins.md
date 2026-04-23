---
title: PROC SQL joins
loaded_when: '"INNER JOIN", "LEFT JOIN", "RIGHT JOIN", "FULL JOIN", "cross join", "Cartesian", "a.*, b.*", "coalesce", "join claims", or any multi-table PROC SQL authoring / debugging.'
---

## Critical Rules

### Rule 1: Always qualify shared columns in multi-table SELECT lists — never `a.*, b.*` with overlapping names

When two joined tables share a column name other than the join key
(common in claims data — `member_id`, `service_dt`, `dx_code`), the
SELECT list must either qualify each column with its table alias or
`COALESCE` them. A bare `a.*, b.*` writes both into the output,
overlaying one silently when the target name collides.

```sas
/* CORRECT - qualify or coalesce every shared column */
proc sql;
  create table claims_plus_elig as
  select c.member_id,
         c.service_dt,
         c.paid_amt,
         coalesce(c.dx_code, e.dx_code) as dx_code,
         e.plan_id
  from claims as c
  left join eligibility as e
    on c.member_id = e.member_id
   and c.service_dt between e.eff_dt and e.term_dt;
quit;
```

```sas
/* WRONG - b.dx_code silently overlays a.dx_code when both exist */
proc sql;
  create table claims_plus_elig as
  select c.*, e.*
  from claims as c
  left join eligibility as e
    on c.member_id = e.member_id;
quit;
```

### Rule 2: `FULL JOIN` requires `COALESCE` on the join key — SAS does not merge it automatically

In a `FULL JOIN`, unmatched rows on either side carry a missing value
for the other side's columns, including the join key. If you select
`a.id` only, rows that exist only in `b` come out with `id = .` — and
vice versa. Always `coalesce(a.id, b.id) as id` in the SELECT list.

```sas
/* CORRECT - coalesce the key so both sides populate it */
proc sql;
  create table combined as
  select coalesce(a.id, b.id) as id,
         a.amount as amount_a,
         b.amount as amount_b
  from a
  full join b on a.id = b.id;
quit;
```

```sas
/* WRONG - rows that exist only in b come out with id missing */
proc sql;
  create table combined as
  select a.id, a.amount as amount_a, b.amount as amount_b
  from a
  full join b on a.id = b.id;
quit;
```

## Canonical Idiom: Left-join reference-table lookup with `COALESCE` defaulting

Attach a reference-table attribute (`plan_type` from the eligibility
roster) to every claim while preserving claims that have no eligibility
match. `COALESCE` supplies a sentinel when the lookup misses.

```sas
proc sql;
  create table claims_plus as
  select c.member_id,
         c.service_dt,
         c.paid_amt,
         coalesce(e.plan_type, 'UNKNOWN') as plan_type
  from claims as c
  left join eligibility as e
    on c.member_id = e.member_id
   and c.service_dt between e.eff_dt and e.term_dt;
quit;
```

## Quick Ref

| Name | Syntax | Purpose | Common mistake |
|------|--------|---------|----------------|
| `INNER JOIN` | `a inner join b on a.k = b.k` | Matched-rows-only join | Writing `a, b where a.k = b.k` and forgetting one predicate → Cartesian |
| `LEFT JOIN` | `a left join b on a.k = b.k` | Keep all rows from `a` | Relying on `b.*` to surface — unmatched rows have missing |
| `FULL JOIN` | `a full join b on a.k = b.k` | Keep all rows from both sides | Not coalescing the join key (Rule 2) |
| `COALESCE` | `coalesce(a, b, c)` | First non-missing | Forgetting it's non-short-circuit — all args evaluated |

## Silent Pitfalls

- **Cartesian from a missing join predicate** — `FROM a, b WHERE a.k =
  b.k AND <other pred>` — if `<other pred>` is a typo that resolves to
  a row-level filter instead of a join predicate, you still get a
  many-to-many on the first clause. Use `FEEDBACK` (see
  `reset-and-options.md`) to surface the expanded query before it runs.

- **`a.*, b.*` overlay** — same-named non-key columns from two tables
  overwrite silently in the output dataset; there is no warning.

## Anti-patterns

- `select a.*, b.* from a join b on a.k = b.k;` where `a` and `b`
  share columns other than `k` → Rule 1; downstream users will hit the
  overlay silently.
- `full join` without `coalesce` on the join key → Rule 2; unmatched
  rows on one side come out with key missing.
- Unqualified comma-join (`from a, b where a.k = b.k`) with more than
  two tables and a partial WHERE predicate list → silent Cartesian
  the moment one predicate is missing.

See `../data-step/sql-vs-merge.md` for how these semantics differ from
DATA-step MERGE (which overwrites rather than producing ambiguous
references).
