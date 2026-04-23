---
title: PROC SQL deduplication
loaded_when: '"SELECT DISTINCT", "GROUP BY", "HAVING" used for dedup, "earliest row per key", "one row per member", "NODUPKEY vs DISTINCT", or any PROC SQL dedup task.'
---

## Critical Rules

### Rule 3: `WHERE` filters rows before grouping; `HAVING` filters groups after

A `WHERE` clause applies to the raw rows prior to `GROUP BY`
aggregation; `HAVING` applies to the grouped summary. Putting an
aggregate-reference (`count(*) >= 10`) in `WHERE` is a syntax error;
putting a row-level predicate (`service_dt > '01JAN2023'd`) in `HAVING`
works but forces SAS to aggregate rows that would have been filtered
out — slower, and the result can silently change if the aggregate
includes the filtered rows.

```sas
/* CORRECT - row filter in WHERE, group filter in HAVING */
proc sql;
  create table frequent_dx as
  select dx_code, count(*) as n_claims
  from claims
  where service_dt between '01JAN2023'd and '31DEC2023'd
  group by dx_code
  having calculated n_claims >= 10;
quit;
```

```sas
/* WRONG - HAVING filters aggregates; a non-aggregate predicate like
   service_dt between '01JAN2023'd and '31DEC2023'd placed in HAVING
   triggers SAS's remerge behavior (or a "Column not in a group" error
   depending on SAS version) rather than filtering input rows before
   aggregation. */
proc sql;
  create table frequent_dx as
  select dx_code, count(*) as n_claims
  from claims
  group by dx_code
  having calculated n_claims >= 10
     and service_dt between '01JAN2023'd and '31DEC2023'd;
quit;
```

## Canonical Idiom: Claims dedup by earliest-row-per-key via `MIN(date)` + self-join

Keep one row per `member_id` — the one with the earliest `service_dt`.
A `GROUP BY` aggregate alone gives you the key and the min date but
loses the other columns; the canonical fix is a self-join between the
aggregate and the detail.

```sas
proc sql;
  create table first_claim as
  select c.*
  from claims as c
  inner join (
    select member_id, min(service_dt) as first_dt
    from claims
    group by member_id
  ) as f
    on c.member_id = f.member_id
   and c.service_dt = f.first_dt;
quit;
```

## SELECT DISTINCT vs PROC SORT NODUPKEY

| Pattern | When to prefer |
|---------|----------------|
| `select distinct key, ... from t` | You need dedup plus a column projection / filter in one pass; output order not required |
| `proc sort data=t out=u nodupkey; by key;` | You need a sorted output and dedup together; or dataset is already BY-sorted and you want to keep physical order from the SORT |
| `proc sort ... noduprecs` | Exact-duplicate removal (every column matches), not key-level dedup |

Cross-topic: see `../base-procs/proc-sort.md` for `NODUPKEY` vs
`NODUPRECS` and BY-group interaction.

## Quick Ref

| Name | Syntax | Purpose | Common mistake |
|------|--------|---------|----------------|
| `SELECT DISTINCT` | `select distinct key from t;` | De-duplicate on selected columns | Using `distinct *` when only some columns matter |
| `GROUP BY` | `group by col1, col2;` | Aggregate key | Selecting a non-aggregated column not in GROUP BY → "remerge" |
| `HAVING` | `having count(*) >= 10;` | Group-level filter | Putting a row-level predicate in `HAVING` (use `WHERE`) |
| `WHERE` | `where cond;` (before GROUP BY) | Row-level filter | Putting an aggregate in `WHERE` (use `HAVING`) |

## Silent Pitfalls

- **Remerged statistics** — selecting a non-aggregated column with a
  `GROUP BY` and an aggregate function. SAS silently remerges the
  summary onto every detail row and prints a NOTE ("The query requires
  remerging summary statistics back with the original data"). Intended
  ~10% of the time; an unintended silent 100x row multiplication the
  rest.
- **`ORDER BY` does not survive `CREATE TABLE AS`** — the created
  table's physical row order is not guaranteed without a trailing
  `ORDER BY`, and even then SAS may reorder via engine. If you need
  deterministic order downstream, store the order via an explicit
  sequence column.

## Anti-patterns

- Aggregate reference (`count(*) >= 10`) in a `WHERE` → Rule 3; SAS
  errors out unambiguously, but putting a row-level predicate in
  `HAVING` is the mirror-image silent bug.
- `select distinct *` on a wide table when you only need key-level
  dedup — slower and masks the intent.
- Dedup by `group by member_id` + `select member_id, min(service_dt),
  other_col` without a self-join — triggers remerge silently.
