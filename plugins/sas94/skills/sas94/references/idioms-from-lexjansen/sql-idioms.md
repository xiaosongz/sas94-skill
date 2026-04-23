---
title: Lafler PROC SQL idioms (WUSS 2011, MWSUG 2015)
loaded_when: "Lafler PROC SQL", searched vs simple CASE, inline CASE expression bucketing, `LEFT JOIN` + `COALESCE` reference-table attach, ambiguous-column overlay trap in PROC SQL joins.
---

## Critical Rules

### Rule: Searched CASE is the general form; simple CASE is for equality buckets only — prefer searched when in doubt

Lafler: "the searched case expression offers the greatest flexibility
and is the primary form used by SQL'ers." The simple form
(`CASE col WHEN value THEN ...`) only handles equality against one
column; any range check, any combination of columns, any `UPCASE()`
wrap falls out of its grammar. Default to the searched form
(`CASE WHEN <full predicate> THEN ...`) unless you are genuinely
mapping one column to equality-based buckets. (Lafler, WUSS 2011.)

```sas
/* CORRECT - searched CASE, combines two columns + a range predicate */
proc sql;
  create table claims_tagged as
  select member_id, service_dt, paid_amt,
    case
      when upcase(category) = 'INPATIENT'
        and paid_amt between 1000 and 10000  then 'inpt-mid'
      when upcase(category) = 'INPATIENT'
        and paid_amt >  10000                then 'inpt-high'
      when upcase(category) = 'OUTPATIENT'   then 'outpt'
      else                                        'other'
    end as claim_bucket
  from claims;
quit;
```

```sas
/* WRONG - simple CASE cannot express a range predicate on LENGTH.
   Unlike most WRONG examples in this skill, this one does NOT run -
   PROC SQL raises a syntax ERROR at parse time:
     ERROR 22-322: Syntax error, expecting one of the following: !, !!,
                   ..., <numeric literal>, <string literal>, ... .
   The simple CASE grammar (`CASE col WHEN value THEN ...`) only accepts
   equality values, never comparison operators. Rewrite as searched CASE
   (`CASE WHEN col < 120 THEN ...`). */
proc sql;
  select title, length,
    case length
      when < 120 then 'Short'
      when > 160 then 'Long'
      else            'Medium'
    end as movie_bucket
  from movies;
quit;
```

## Canonical Idioms

### Idiom: Lafler `LEFT JOIN` + `COALESCE` for reference-table attach

Lafler's MWSUG 2015 paper walks the full match-join matrix (inner,
left outer, right outer, full). The canonical claims-data form is
`LEFT JOIN` from the driver to a reference or eligibility table, with
`COALESCE` supplying a sentinel where the reference misses. Unlike
the DATA-step MERGE, Lafler notes that PROC SQL's "duplicate matching
column is not automatically overlaid" — meaning every shared column
must be qualified or coalesced in the SELECT or you get an ambiguous
reference at best, a silent overlay at worst. (Lafler, MWSUG 2015.)

```sas
proc sql;
  create table claims_plus as
  select c.member_id,
         c.service_dt,
         c.paid_amt,
         coalesce(e.plan_type, 'UNKNOWN') as plan_type
  from claims as c
  left join eligibility as e
    on  c.member_id  = e.member_id
   and c.service_dt between e.eff_dt and e.term_dt;
quit;
```

### Idiom: Lafler searched CASE for inline claim-cost bucketing

Lafler's WUSS 2011 paper makes searched CASE the primary conditional
tool inside PROC SQL — "similar to an IF-THEN construct in the DATA
step, a case expression uses one or more WHEN-THEN clause(s) to
conditionally process some but not all the rows." The form is
cleaner than a secondary DATA step and keeps the bucketing logic
adjacent to the SELECT that uses it. Always include an `ELSE`; Lafler
stresses this as the "catch-all to prevent a missing value from being
assigned." In claims work the pattern attaches paid-amount buckets,
age bands, or LOS categories without a second pass. (Lafler, WUSS
2011.)

```sas
proc sql;
  create table claims_tagged as
  select member_id,
         service_dt,
         paid_amt,
         case
           when paid_amt  =  0                         then 'zero-pay'
           when paid_amt  <  100                       then 'low'
           when paid_amt  <  1000                      then 'mid'
           when paid_amt  <  10000                     then 'high'
           else                                             'catastrophic'
         end as amt_bucket
  from claims;
quit;
```

## Silent Pitfalls

- **Simple CASE with range predicates** — Lafler's WUSS paper shows
  `CASE length WHEN < 120 THEN ...` as an anti-example: the simple
  form only handles equality. Use searched CASE when the predicate
  is anything richer than `col = value`.
- **Shared non-key columns in a join** — PROC SQL does not
  auto-overlay like DATA-step MERGE; qualify or `COALESCE` every
  shared column in the SELECT or you get an ambiguous reference (or
  worse, a silent single-side pick).

## Anti-patterns (STOP signs)

- `case col when < 120 then ...` — simple CASE grammar does not
  accept a comparison operator; rewrite as searched CASE.
- `left join b on a.k = b.k` followed by `select a.*, b.*` where
  both tables have a shared non-key column — silent overlay of one
  column onto the other. See `../proc-sql/joins.md` for the
  qualifier / COALESCE remedy.
- Citing `lafler-2011-sgf-procsql-tips.md` in this repo — the
  cached file at that path contains Gamishev's SGF 2011 paper 101
  on email management, not Lafler. Use the two cited Lafler papers
  (WUSS 2011 and MWSUG 2015) instead.

Cross-refs: `../proc-sql/joins.md`, `../proc-sql/case-expressions.md`,
`../data-step/sql-vs-merge.md`.
