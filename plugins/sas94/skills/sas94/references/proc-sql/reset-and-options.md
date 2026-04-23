---
title: PROC SQL RESET, NOEXEC, FEEDBACK, and query-level options
loaded_when: '"RESET", "FEEDBACK", "NOEXEC", "NUMBER", "NOPROMPT", "NOWARNRECURS", PROC SQL debugging / dry-run, "expand * into column list", or "why did this SQL run in batch but not interactively".'
---

## Critical Rules

### Rule 5: Use `FEEDBACK` to surface the expanded query — catches `*` expansion and outer-reference bugs before execution

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

## Quick Ref

| Name | Syntax | Purpose | Common mistake |
|------|--------|---------|----------------|
| `FEEDBACK` | `proc sql feedback;` | Log expanded query pre-exec | Turning on for an entire batch — log floods |
| `NOEXEC` | `proc sql noexec;` | Parse / plan without running | Running with side-effecting DDL (`CREATE TABLE` still validates) |
| `RESET` | `reset feedback noexec;` (inside a PROC SQL block) | Change options mid-block | Expecting scope to outlive the `quit;` |
| `CREATE TABLE AS` | `create table t as select ...;` | Materialize a query in one pass | Using empty-create + INSERT when AS would do |
| `INSERT INTO` | `insert into t select ...;` or `insert into t values(...);` | Append rows to an existing table | Mismatched column count / type vs the target |
| `UPDATE` | `update t set col = expr where ...;` | In-place row modification | Forgetting `WHERE` → every row updated |
| `DELETE` | `delete from t where ...;` | Remove rows | Forgetting `WHERE` → every row deleted |
| `ORDER BY` | `order by col1 desc, col2;` | Sort result set | Assuming CREATE TABLE AS preserves ORDER BY without one |

## Silent Pitfalls

- **Interactive vs batch `RESET` drift** — an interactive session
  carries the last `RESET` state across PROC SQL blocks; batch does not.
  Code that "worked in SAS/Studio" then fails in a batch submit is
  almost always a forgotten `reset feedback` / `reset noexec`.
- **`NOEXEC` does not block DDL validation side-effects** — `CREATE
  TABLE ... AS SELECT` is validated (including resolving every column),
  so schema changes that would fail at runtime still surface, but
  certain engine-specific DDL paths can partially execute. Treat
  `NOEXEC` as "no data read", not "zero side-effects".
- **`FEEDBACK` floods the log in batch** — leave it off by default and
  turn on with `RESET` only around the suspect query.

## Anti-patterns

- `create table t (cols ...); insert into t select ...;` when a single
  `create table t as select ...` would do — Rule 8; two passes and
  loses inferred attributes.
- Shipping a pipeline with `FEEDBACK` globally on — log bloat hides
  real warnings.
- Relying on an interactive session's lingering `RESET` state — always
  be explicit inside the block.
