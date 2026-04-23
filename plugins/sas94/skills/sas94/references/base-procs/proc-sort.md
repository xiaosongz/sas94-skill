---
title: PROC SORT — NODUPKEY vs NODUPRECS, OUT= overwrite
loaded_when: '"PROC SORT", "NODUPKEY", "NODUPRECS", "DUPOUT=", "BY statement sort", "in-place sort", "dedup", "deduplicate", or "sort silently overwrites input".'
---

## Critical Rules

### Rule 3: `PROC SORT NODUPKEY` dedups on BY vars only — `NODUPRECS` dedups on the full row

`NODUPKEY` keeps the first observation per `BY` group and drops the
rest — even if the other columns differ. `NODUPRECS` only drops an
observation when **every column** equals the adjacent one. Mixing them
up is a common "where did my data go?" source; use `DUPOUT=` to catch
the dropped rows for audit.

```sas
/* CORRECT - deliberate: one row per member_id, log dropped dups */
proc sort data=claims out=claims_one_per_member
          nodupkey dupout=claims_dupes;
  by member_id;
run;
```

```sas
/* WRONG - expects full-row dedup but NODUPKEY keeps only one per member_id */
proc sort data=claims out=claims_dedup nodupkey;
  by member_id;
run;
/* claims with the same member_id but different service_dt → all but first lost */
```

### Rule 4: `PROC SORT` without `OUT=` **replaces** the input dataset in place

`proc sort data=claims; by member_id; run;` overwrites `claims` with
the sorted version. In an interactive session this is fine; in a
pipeline it destroys the original ordering (which may have been
meaningful — file-order from an SFTP drop, for instance). Always
specify `OUT=` unless the in-place sort is deliberate.

```sas
/* CORRECT - out= preserves the input */
proc sort data=claims out=claims_sorted;
  by member_id service_dt;
run;
```

```sas
/* WRONG - silently overwrites work.claims */
proc sort data=claims;
  by member_id service_dt;
run;
```

## Canonical Idiom: NODUPKEY dedup with audit tail

Purpose: dedup claims to one row per `member_id` + `service_dt`, but
preserve the duplicates in a separate dataset for QA review. `DUPOUT=`
captures exactly the rows that `NODUPKEY` discards.

```sas
proc sort data=claims
          out=claims_unique
          nodupkey
          dupout=claims_dupes;
  by member_id service_dt;
run;
```

## Quick Ref

| Option | Purpose | Common mistake |
|--------|---------|----------------|
| `out=b` | Write sorted copy, preserve input | Omitting → silently overwrites input |
| `by v1 v2;` | Sort keys | Wrong order → downstream MERGE/BY fails |
| `nodupkey` | Keep first per BY group | Mistaking for full-row dedup |
| `noduprecs` | Drop fully-duplicated adjacent rows | Only adjacent — sort first |
| `dupout=d` | Audit dataset of dropped rows | Forgetting → discarded silently |
| `descending v` | Reverse sort on one key | Applies only to the next BY var |

## Anti-patterns (STOP signs)

- `proc sort data=claims; by ...; run;` with no `OUT=` → overwrites
  `claims`.
- `proc sort nodupkey; by member_id; run;` expecting full-row dedup →
  all but first row per `member_id` lost.

Cross-ref: DATA-step `first.`/`last.` + `if first.key` gives the
same dedup with full control — see `../data-step/retain-pdv.md`.
For SQL `SELECT DISTINCT` alternative see the PROC SQL reference.
