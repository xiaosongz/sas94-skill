---
title: Canonical hash-object idioms
loaded_when: 'streaming reference lookup, Dorfman dedup, in-memory counter / aggregator, one-to-many hash join, hash idiom, "attach description", "first visit", "tally per key".'
---

## Canonical Idioms

### Idiom: Reference-table lookup — attach ICD-10 description to every claim row

Purpose: the bread-and-butter many-to-one hash lookup — pull a
descriptive column from a small reference table onto every row of a
large driver dataset without pre-sorting either side. The
`if 0 then set` trick gives the PDV the right column types for
parameter-type matching without actually reading a row.

```sas
data claims_labeled;
  length dx_desc $60 chapter $8;
  if _N_ = 1 then do;
    if 0 then set icd10_ref;
    declare hash ref(dataset: 'icd10_ref');
    ref.definekey('dx_code');
    ref.definedata('dx_desc', 'chapter');
    ref.definedone();
    call missing(dx_desc, chapter);
  end;
  set claims;
  if ref.find() ne 0 then do;
    dx_desc = 'UNMAPPED';
    chapter = 'UNK';
  end;
run;
```

### Idiom: Deduplication via `check()` + `add()` — keep the first row per composite key

Purpose: stream a large dataset once, keeping only the first row per
(pat_id, service_dt) composite key. `check()` returns 0 on a hit
without modifying the hash — so you can ask "have I seen this key?"
without consuming a slot, then `add()` the new key on a miss and
output the row. No pre-sort required.

```sas
data first_visit;
  if _N_ = 1 then do;
    declare hash seen();
    seen.definekey('pat_id', 'service_dt');
    /* no definedata() — key-only hash; check()/add() need only the key
       to answer "have I seen this composite key before?". */
    seen.definedone();
  end;
  set claims;
  if seen.check() ne 0 then do;
    seen.add();
    output;
  end;
run;
```

### Idiom: In-memory counter — tally per-key frequencies with `find()` + `replace()`

Purpose: count occurrences per key without an explicit PROC FREQ +
re-sort pass. On a miss, initialize the count to 1 and `add()`; on a
hit, increment and `replace()`. `h.output()` persists the final
counts to a dataset. Useful for claims-volume rollups where the
grouping column has modest cardinality (dx_code, provider_npi).

```sas
data _null_;
  if _N_ = 1 then do;
    declare hash cnt();
    cnt.definekey('dx_code');
    cnt.definedata('dx_code', 'n');
    cnt.definedone();
  end;
  set claims end=eof;
  if cnt.find() = 0 then do;
    n + 1;
    cnt.replace();
  end;
  else do;
    n = 1;
    cnt.add();
  end;
  if eof then cnt.output(dataset: 'dx_counts');
run;
```

### Idiom: One-to-many equi-join via `multidata: 'Y'` + `find_next()`

Purpose: join a claims driver to an eligibility table with multiple
rows per member (one per coverage span). With `multidata: 'Y'`, the
hash accepts duplicate keys; `find()` retrieves the first match,
`find_next()` walks the remaining entries for the same key. The
`do while (rc = 0)` loop outputs one row per match — equivalent to a
PROC SQL inner join without a sort.

```sas
data claim_x_elig;
  if _N_ = 1 then do;
    if 0 then set eligibility;
    declare hash e(dataset: 'eligibility', multidata: 'Y');
    e.definekey('member_id');
    e.definedata('plan_id', 'eff_dt', 'term_dt');
    e.definedone();
  end;
  set claims;
  rc = e.find();
  do while (rc = 0);
    if eff_dt <= service_dt <= term_dt then output;
    rc = e.find_next();
  end;
run;
```

Cross-references: `PROC SORT NODUPKEY` is the alternative to the
`check()` + `add()` dedup idiom when pre-sorting is acceptable —
see `../base-procs/proc-sort.md`. The PROC SQL reference covers the
SQL-join alternative when the lookup table does not fit in memory.
