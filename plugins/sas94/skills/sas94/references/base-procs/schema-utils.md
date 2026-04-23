---
title: PROC CONTENTS + PROC DATASETS (incl. KILL destructive trap)
loaded_when: '"PROC CONTENTS", "PROC DATASETS", "schema inspection", "library cleanup", "DELETE statement", "KILL option", "MODIFY RENAME LABEL", "NOLIST", or "library metadata".'
---

## Critical Rules

### Rule 9: Use `PROC CONTENTS` for schema inspection; `PROC DATASETS` for metadata + deletion — `KILL` empties a library without confirmation

`PROC CONTENTS` is the read-only path — column names, types, lengths,
formats, labels, sort order, observation count. `PROC DATASETS` is the
metadata-edit path — rename, relabel, reformat, add/drop indexes, and
delete datasets. `DATASETS` treats all requested deletes as silent:
`KILL` empties the entire library without a confirmation prompt,
`DELETE ds1 ds2;` drops the named datasets with only a NOTE in the log.
Use `NOLIST` in interactive sessions to suppress the default directory
listing.

```sas
/* CORRECT - inspect schema of a single dataset */
proc contents data=work.claims;
run;

/* CORRECT - selectively delete named datasets, quiet */
proc datasets lib=work nolist;
  delete claims_tmp1 claims_tmp2 members_tmp;
quit;

/* CORRECT - rename/relabel without re-writing the dataset */
proc datasets lib=work nolist;
  modify claims;
    rename paid_amt = paid_amt_usd;
    label  paid_amt_usd = 'Total Paid (USD)';
quit;
```

```sas
/* WRONG - KILL empties the whole library with no confirmation */
proc datasets lib=work kill nolist;
quit;
/* Every dataset in WORK is gone. No WARNING, no prompt. */
```

## Quick Ref

| Proc / statement | Purpose | Common mistake |
|------------------|---------|----------------|
| `proc contents data=lib.ds;` | Schema + metadata dump | Using `data=lib._all_` → floods output |
| `proc contents data=lib._all_ nods;` | Directory listing only | Omitting `nods` → one page per dataset |
| `proc datasets lib=work nolist;` | Metadata-edit session | Omitting `nolist` → always prints listing |
| `delete ds1 ds2;` | Selective drop | Typos delete wrong dataset silently |
| `modify ds; rename a=b;` | Rename without rewriting | Index / constraints may need rebuild |
| `kill` (PROC option) | Empty entire library | **NO PROMPT** — destroys everything |

## Anti-patterns (STOP signs)

- `proc datasets lib=<lib> kill;` on a production or shared library →
  destroys every dataset; there is no confirmation and no tombstone.
- `proc contents data=lib._all_;` without `nods` → one schema page per
  dataset; floods the listing.
