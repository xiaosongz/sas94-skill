---
title: PROC SQL reference
scope: Joins, deduplication, `INTO :macvar` list targets, dictionary tables, `RESET` / `FEEDBACK` / `NOEXEC` diagnostics, and claims-style multi-table SQL idioms.
loaded_when: '"PROC SQL", "SELECT", "LEFT JOIN" / "INNER JOIN" / "FULL JOIN", "INTO :", "dictionary.", "join claims", "dedup", or any PROC SQL authoring or debugging task.'
last_reviewed: 2026-04-21
reviewer: xiaosongz
---

## Overview

PROC SQL is Base SAS's implementation of ANSI SQL with SAS-specific
extensions for dataset options, formats, functions, and macro-variable
plumbing. Unlike the DATA-step MERGE, a PROC SQL join does not require
pre-sorting, does not overwrite same-named columns silently (they become
ambiguous references instead), and can combine up to 256 tables in a
single query. That flexibility is also where most bugs come from: a
missed `DISTINCT`, an unqualified column in an outer join, or an
`INTO :list` that ships an un-trimmed macro variable into an `IN()`
clause.

Most "PROC SQL is slow / wrong" reports resolve to one of three classes:
(1) row explosion from a many-to-many join mistaken for one-to-many,
(2) ambiguous columns in the SELECT list because `a.*, b.*` pulled the
same column from both sides, or (3) a `GROUP BY` / `HAVING` combination
that silently re-merges grouped statistics back onto detail rows (the
"SAS remerge" warning). This file encodes the syntax rules from the
Base SAS Procedures Guide "SQL Procedure" chapter and the three Kirk
Paul Lafler papers on joins, CASE expressions, and tips / techniques.

See also `data-step.md` Idiom "SQL join vs MERGE distinction" for the
step-by-step comparison with DATA-step MERGE semantics.

## Critical Rules

### Rule 1: Always qualify shared columns in multi-table SELECT lists — never `a.*, b.*` with overlapping names

Source: https://www.lexjansen.com/mwsug/2015/RF/MWSUG-2015-RF-02.pdf

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

Source: https://www.lexjansen.com/mwsug/2015/RF/MWSUG-2015-RF-02.pdf

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

### Rule 3: `WHERE` filters rows before grouping; `HAVING` filters groups after

Source: https://documentation.sas.com/doc/en/proc/9.4/proc.htm

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
/* WRONG - row-level filter in HAVING, aggregate runs against all years */
proc sql;
  create table frequent_dx as
  select dx_code, count(*) as n_claims
  from claims
  group by dx_code
  having calculated n_claims >= 10
     and service_dt between '01JAN2023'd and '31DEC2023'd;
quit;
```

### Rule 4: `INTO :macvar SEPARATED BY ','` needs `%trim` / `strip()` before going into an `IN()` clause

Source: https://support.sas.com/resources/papers/proceedings11/101-2011.pdf

`SELECT DISTINCT col INTO :list SEPARATED BY ','` pads the macro
variable to the SQL query's working width. Passing `&list` directly into
a downstream `IN(&list)` works for numerics but fails silently for short
character codes — trailing blanks inside the list cause the `IN` to miss
matches. Always `%let list = %trim(&list);` or `strip()` each element.

```sas
/* CORRECT - bound and trim the list, then use in a downstream query */
proc sql noprint;
  select distinct quote(strip(dx_code))
    into :dx_list separated by ','
  from priority_codes;
quit;
%let dx_list = %sysfunc(compbl(&dx_list));

proc sql;
  create table hits as
  select * from claims where dx_code in (&dx_list);
quit;
```

```sas
/* WRONG - blank-padded codes in the IN() silently miss matches */
proc sql noprint;
  select distinct dx_code
    into :dx_list separated by ','
  from priority_codes;
quit;

proc sql;
  create table hits as
  select * from claims where dx_code in (&dx_list);
quit;
```

### Rule 5: Use `FEEDBACK` to surface the expanded query — catches `*` expansion and outer-reference bugs before execution

Source: https://www.lexjansen.com/wuss/2011/coders/Papers_Lafler_K_72492.pdf

`proc sql feedback;` logs the fully-expanded query (with `*` replaced by
the real column list and outer-query references resolved) before running
it. This is the fastest way to spot a column-name collision or an
unintentional Cartesian before it produces millions of rows.

```sas
/* CORRECT - use FEEDBACK as a pre-execution sanity check */
proc sql feedback;
  create table combined as
  select * from claims as c, eligibility as e
  where c.member_id = e.member_id;
quit;
/* Log shows the expanded column list — cross-join spelled out plainly. */
```

### Rule 6: `NOEXEC` is a dry-run — parses and plans the query without reading data

Source: https://www.lexjansen.com/wuss/2011/coders/Papers_Lafler_K_72492.pdf

`proc sql noexec;` validates syntax and resolves table / column
references without executing. Pair it with `FEEDBACK` in CI to catch
broken queries introduced by a schema change without paying the cost of
running them against the full claims table.

```sas
/* CORRECT - dry-run before shipping the job */
proc sql noexec feedback;
  create table claims_2023 as
  select member_id, service_dt, paid_amt
  from raw.claims
  where year(service_dt) = 2023;
quit;
/* Any typo in member_id, raw.claims, or paid_amt surfaces without a full-table scan. */
```

### Rule 7: `RESET` changes options mid-query block — scope is the current PROC SQL, not the SAS session

Source: https://documentation.sas.com/doc/en/proc/9.4/proc.htm

`reset feedback noexec;` toggles SQL-specific options (`FEEDBACK`,
`NOEXEC`, `NUMBER`, `NOWARNRECURS`, etc.) without ending the PROC SQL
block with `quit;`. Forgotten `reset` is a classic "ran fine
interactively, exploded in batch" source — the interactive session
carries an earlier `reset` that batch does not.

```sas
/* CORRECT - explicit RESET inside the block */
proc sql feedback;
  select * from claims(obs=10);
  reset nofeedback;
  create table claims_2023 as
    select * from claims where year(service_dt) = 2023;
quit;
```

### Rule 8: Prefer `CREATE TABLE t AS SELECT ...` over `CREATE TABLE t (cols)` + `INSERT INTO`

Source: https://www.lexjansen.com/mwsug/2015/RF/MWSUG-2015-RF-02.pdf

A single `CREATE TABLE t AS SELECT ... FROM ...` statement is one pass
over the source. The "create empty table, then insert rows" pattern is
two passes minimum, loses column types / lengths inferred from the
SELECT, and cannot be short-circuited by `NOEXEC`. Use the multi-statement
form only when you need to stage an empty table for a later load.

```sas
/* CORRECT - one-shot CREATE TABLE AS */
proc sql;
  create table claims_2023 as
  select member_id, service_dt, paid_amt
  from raw.claims
  where year(service_dt) = 2023;
quit;
```

```sas
/* WRONG - empty table + INSERT; two passes, loses inferred attrs */
proc sql;
  create table claims_2023 (member_id char(10), service_dt num, paid_amt num);
  insert into claims_2023
    select member_id, service_dt, paid_amt
    from raw.claims where year(service_dt) = 2023;
quit;
```

## Canonical Idioms

### Idiom: Claims dedup by earliest-row-per-key via `MIN(date)` + self-join

Source: https://www.lexjansen.com/mwsug/2015/RF/MWSUG-2015-RF-02.pdf

Purpose: keep one row per `member_id` — the one with the earliest
`service_dt`. A `GROUP BY` aggregate alone gives you the key and the
min date but loses the other columns; the canonical fix is a self-join
between the aggregate and the detail.

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

### Idiom: `INTO :list SEPARATED BY ' '` — build a macro-variable list of column names for dynamic SQL

Source: https://support.sas.com/resources/papers/proceedings11/101-2011.pdf

Purpose: read `dictionary.columns` to build a dynamic column list, then
paste it into a generated SELECT. Common pattern for "select every
numeric variable except the key" style queries.

```sas
proc sql noprint;
  select name
    into :num_vars separated by ' '
  from dictionary.columns
  where libname = 'WORK'
    and memname = 'CLAIMS'
    and type = 'num'
    and upcase(name) ne 'MEMBER_ID';
quit;

proc means data=claims noprint;
  class member_id;
  var &num_vars;
  output out=claims_summary sum= / autoname;
run;
```

### Idiom: Canonical left join — reference-table lookup with `COALESCE` defaulting

Source: https://www.lexjansen.com/mwsug/2015/RF/MWSUG-2015-RF-02.pdf

Purpose: attach a reference-table attribute (`plan_type` from the
eligibility roster) to every claim while preserving claims that have no
eligibility match. `COALESCE` supplies a sentinel when the lookup misses.

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

### Idiom: CASE expression for row-level conditional classification

Source: https://www.lexjansen.com/wuss/2011/coders/Papers_Lafler_K_72492.pdf

Purpose: compute a derived category column inline — cleaner than a
secondary DATA step and keeps the logic next to the SELECT that uses
it. Searched form (no column name after `CASE`) is the general case;
simple form (`CASE col WHEN value THEN ...`) is for equality buckets
only.

```sas
proc sql;
  create table claims_tagged as
  select member_id,
         service_dt,
         paid_amt,
         case
           when paid_amt = 0            then 'zero-pay'
           when paid_amt < 100          then 'low'
           when paid_amt < 1000         then 'mid'
           else                              'high'
         end as amt_bucket
  from claims;
quit;
```

### Idiom: Dictionary-table introspection — list every variable in every WORK dataset

Source: https://documentation.sas.com/doc/en/proc/9.4/proc.htm

Purpose: programmatic schema lookup for generated code or audit. Avoids
hand-maintaining a list of variable names across pipeline stages.

```sas
proc sql;
  create table work_schema as
  select libname, memname, name, type, length, label
  from dictionary.columns
  where libname = 'WORK'
  order by memname, name;
quit;
```

## Function / Statement Quick Ref

| Name | Syntax | Purpose | Common mistake | Doc URL |
|------|--------|---------|----------------|---------|
| `SELECT` | `select col1, col2 from t;` | Project columns from a table | `a.*, b.*` with overlapping column names | [`SELECT`](https://documentation.sas.com/doc/en/proc/9.4/proc.htm) |
| `SELECT DISTINCT` | `select distinct key from t;` | De-duplicate on selected columns | Using `distinct *` when only some columns matter | [`SELECT DISTINCT`](https://documentation.sas.com/doc/en/proc/9.4/proc.htm) |
| `CREATE TABLE AS` | `create table t as select ...;` | Materialize a query in one pass | Using empty-create + INSERT when AS would do | [`CREATE TABLE`](https://documentation.sas.com/doc/en/proc/9.4/proc.htm) |
| `INSERT INTO` | `insert into t select ...;` or `insert into t values(...);` | Append rows to an existing table | Mismatched column count / type vs the target | [`INSERT INTO`](https://documentation.sas.com/doc/en/proc/9.4/proc.htm) |
| `UPDATE` | `update t set col = expr where ...;` | In-place row modification | Forgetting `WHERE` → every row updated | [`UPDATE`](https://documentation.sas.com/doc/en/proc/9.4/proc.htm) |
| `DELETE` | `delete from t where ...;` | Remove rows | Forgetting `WHERE` → every row deleted | [`DELETE`](https://documentation.sas.com/doc/en/proc/9.4/proc.htm) |
| `WHERE` | `where cond;` (before GROUP BY) | Row-level filter | Putting an aggregate in `WHERE` (use `HAVING`) | [`WHERE`](https://documentation.sas.com/doc/en/proc/9.4/proc.htm) |
| `GROUP BY` | `group by col1, col2;` | Aggregate key | Selecting a non-aggregated column not in GROUP BY → "remerge" | [`GROUP BY`](https://documentation.sas.com/doc/en/proc/9.4/proc.htm) |
| `HAVING` | `having count(*) >= 10;` | Group-level filter | Putting a row-level predicate in `HAVING` (use `WHERE`) | [`HAVING`](https://documentation.sas.com/doc/en/proc/9.4/proc.htm) |
| `ORDER BY` | `order by col1 desc, col2;` | Sort result set | Assuming CREATE TABLE AS preserves ORDER BY without one | [`ORDER BY`](https://documentation.sas.com/doc/en/proc/9.4/proc.htm) |
| `INNER JOIN` | `a inner join b on a.k = b.k` | Matched-rows-only join | Writing `a, b where a.k = b.k` and forgetting one predicate → Cartesian | [`INNER JOIN`](https://documentation.sas.com/doc/en/proc/9.4/proc.htm) |
| `LEFT JOIN` | `a left join b on a.k = b.k` | Keep all rows from `a` | Relying on `b.*` to surface — unmatched rows have missing | [`LEFT JOIN`](https://documentation.sas.com/doc/en/proc/9.4/proc.htm) |
| `FULL JOIN` | `a full join b on a.k = b.k` | Keep all rows from both sides | Not coalescing the join key (Rule 2) | [`FULL JOIN`](https://documentation.sas.com/doc/en/proc/9.4/proc.htm) |
| `INTO :mv` | `select col into :mv from t;` | Write a scalar into a macro variable | Forgetting `NOPRINT` on the PROC SQL | [`INTO :`](https://documentation.sas.com/doc/en/proc/9.4/proc.htm) |
| `INTO :mv SEPARATED BY` | `select col into :mv separated by ',' from t;` | Build a delimited list macro var | Not trimming before pasting into `IN()` (Rule 4) | [`INTO :mv SEPARATED BY`](https://documentation.sas.com/doc/en/proc/9.4/proc.htm) |
| `CASE` | `case when cond then val else val end as name` | Row-level conditional | Missing `ELSE` → rows get missing value silently | [`CASE expression`](https://documentation.sas.com/doc/en/proc/9.4/proc.htm) |
| `COALESCE` | `coalesce(a, b, c)` | First non-missing | Forgetting it's non-short-circuit — all args evaluated | [`COALESCE`](https://documentation.sas.com/doc/en/proc/9.4/proc.htm) |
| `DICTIONARY.COLUMNS` | `select ... from dictionary.columns where libname='...'` | Schema introspection | Using `sashelp.vcolumn` (view over the same) in PROC SQL — fine, but slower | [`DICTIONARY`](https://documentation.sas.com/doc/en/proc/9.4/proc.htm) |
| `FEEDBACK` | `proc sql feedback;` | Log expanded query pre-exec | Turning on for an entire batch — log floods | [`FEEDBACK`](https://documentation.sas.com/doc/en/proc/9.4/proc.htm) |
| `NOEXEC` | `proc sql noexec;` | Parse / plan without running | Running with side-effecting DDL (`CREATE TABLE` still validates) | [`NOEXEC`](https://documentation.sas.com/doc/en/proc/9.4/proc.htm) |
| `RESET` | `reset feedback noexec;` (inside a PROC SQL block) | Change options mid-block | Expecting scope to outlive the `quit;` | [`RESET`](https://documentation.sas.com/doc/en/proc/9.4/proc.htm) |

## Silent Pitfalls

- **Remerged statistics** — selecting a non-aggregated column with a
  GROUP BY and an aggregate function. SAS silently remerges the summary
  onto every detail row and prints a NOTE ("The query requires remerging
  summary statistics back with the original data"). Intended ~10% of the
  time; an unintended silent 100x row multiplication the rest.
  Source: https://documentation.sas.com/doc/en/proc/9.4/proc.htm

- **Cartesian from a missing join predicate** — `FROM a, b WHERE a.k =
  b.k AND <other pred>` — if `<other pred>` is a typo that resolves to
  a row-level filter instead of a join predicate, you still get a
  many-to-many on the first clause. `FEEDBACK` (Rule 5) surfaces this.
  Source: https://www.lexjansen.com/mwsug/2015/RF/MWSUG-2015-RF-02.pdf

- **`INTO :list` trailing blanks** — character-list macvars pick up
  blank padding from the longest element's storage length, not the
  visible content. Downstream `IN(&list)` misses matches for shorter
  codes. Always strip / trim before use (Rule 4).
  Source: https://support.sas.com/resources/papers/proceedings11/101-2011.pdf

- **`ORDER BY` does not survive `CREATE TABLE AS`** — the created
  table's physical row order is not guaranteed without a trailing
  `ORDER BY` and even then SAS may reorder via engine. If you need
  deterministic order downstream, store the order via an explicit
  sequence column.
  Source: https://documentation.sas.com/doc/en/proc/9.4/proc.htm

## Anti-patterns (STOP signs)

**STOP** when you see any of the following — the code compiles and
returns rows, but the rows are almost certainly not what the author
meant:

- `select a.*, b.* from a join b on a.k = b.k;` where `a` and `b`
  share columns other than `k` → see Rule 1; downstream users will hit
  the overlay silently.
- `full join` without `coalesce` on the join key → see Rule 2; unmatched
  rows on one side come out with key missing.
- Aggregate reference (`count(*) >= 10`) in a `WHERE` → see Rule 3; SAS
  errors out unambiguously, but putting a row-level predicate in
  `HAVING` is the mirror-image silent bug.
- `select ... into :list separated by ','` from character source with
  no `strip()` / `%trim`, then `where col in (&list)` → see Rule 4.
- `create table t (cols ...); insert into t select ...;` when a single
  `create table t as select ...` would do — see Rule 8; two passes and
  loses inferred attributes.

## See Also

- [data-step.md](data-step.md) — "SQL join vs MERGE distinction" idiom
  (GWU §4) and DATA-step MERGE overwrite semantics.
- [base-procs.md](base-procs.md) — `PROC SORT NODUPKEY` vs SQL
  `SELECT DISTINCT` dedup comparison.
- [macros.md](macros.md) — macro-variable side of `INTO :mv` and
  `call symputx` / `symget`.
- [idioms-from-lexjansen.md](idioms-from-lexjansen.md) — deeper PROC
  SQL + DATA-step treatments from Lafler and other SUGI / WUSS papers.
- [Base SAS Procedures Guide — SQL Procedure](https://documentation.sas.com/doc/en/proc/9.4/proc.htm)
- [Lafler (2015) — Essential PROC SQL Join Techniques](https://www.lexjansen.com/mwsug/2015/RF/MWSUG-2015-RF-02.pdf)
- [Lafler (2011) — Conditional Processing Using the Case Expression in PROC SQL](https://www.lexjansen.com/wuss/2011/coders/Papers_Lafler_K_72492.pdf)
