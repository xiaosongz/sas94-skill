---
title: Dorfman hash idioms (SUGI 30, NESUG 2007, SESUG 2015)
loaded_when: "Dorfman hash", hash object idiom, streaming lookup against a large driver, `check()`+`add()` dedup, hash-based aggregation / `find()`+`replace()` counter, `multidata: 'Y'` + `find_next()` one-to-many join, OOM from loading the wrong side into hash.
---

## Critical Rules

### Rule: Load the SMALL side into the hash and stream the LARGE side with `set` — never the other way round

Dorfman's Hash Crash paper is explicit: the hash object is a
memory-resident table whose footprint is the loaded rowcount times the
key + data portion width. Claims-data pipelines tempt the wrong
choice because the reference table (ICD-10, NDC, provider roster) is
always the small one, but Dorfman's examples show learners routinely
load the driver — a 10-50M-row claims extract — and OOM the session.
The rule: reference in the hash, driver through `set`. (Dorfman,
NESUG 2007.)

```sas
/* CORRECT - 70k-row ICD-10 reference in hash, 50M-row claims streamed */
if _N_ = 1 then do;
  declare hash ref(dataset: 'icd10_ref');
  ref.definekey('dx_code');
  ref.definedata('dx_desc', 'chapter');
  ref.definedone();
end;
set claims;                 /* streamed, one row at a time */
rc = ref.find();
```

```sas
/* WRONG - 50M-row claims loaded into the hash; process OOMs */
if _N_ = 1 then do;
  declare hash big(dataset: 'claims');
  big.definekey('claim_id');
  big.definedata('paid_amt', 'service_dt', 'dx_code');
  big.definedone();
end;
set icd10_ref;
rc = big.find();
```

## Canonical Idioms

### Idiom: Dorfman streaming reference-table lookup

Paul Dorfman's SUGI 30 paper establishes the canonical many-to-one
hash lookup: load a small reference table into a hash on `_N_ = 1`,
then `set` the large driver dataset and call `find()` per row. The
PDV is type-matched with `if 0 then set ref;` — a no-op that populates
column types without reading a row. Dorfman frames this as the hash's
defining use case: "Attaching a descriptive column from a small
reference table onto every row of a large driver dataset without
pre-sorting either side." Claims-data version: ICD-10 description
table -> claims; provider NPI roster -> encounters. (Dorfman, SUGI 30
2005.)

```sas
data claims_labeled;
  length dx_desc $60 chapter $8;
  if _N_ = 1 then do;
    if 0 then set icd10_ref;                /* type-match PDV */
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

### Idiom: Dorfman MULTIDATA + `find_next()` for one-to-many joins

Dorfman's 2015 SESUG paper covers the duplicate-key extension: with
`multidata: 'Y'` the hash accepts multiple entries per key, and
`find_next()` walks the duplicates for the current key. The classic
claims-data scenario is joining a claims driver to an eligibility
table that has one row per member per coverage span. Without
`multidata: 'Y'` only the first span survives; with it, a
`do while (rc = 0)` loop emits one output row per span, matching a
PROC SQL inner join without the sort. (Dorfman, SESUG 2015.)

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

### Idiom: Dorfman `check()` + `add()` deduplication

From the Hash Crash NESUG 2007 paper: the canonical "stream once,
keep the first row per composite key" idiom. `check()` asks "have I
seen this key?" without modifying the hash; `add()` inserts the new
key and the row is emitted. No pre-sort, no `NODUPKEY` pass — a
single DATA step over the driver. Useful in claims data for
"first-visit-per-patient" or "first-claim-per-provider-per-day"
deduplication where a PROC SORT would cost an extra pass over tens
of millions of rows. (Dorfman, NESUG 2007.)

```sas
data first_visit;
  if _N_ = 1 then do;
    declare hash seen();
    seen.definekey('pat_id', 'service_dt');
    /* no definedata() - key-only hash; check()/add() test and insert
       membership without copying any data portion into the PDV. */
    seen.definedone();
  end;
  set claims;
  if seen.check() ne 0 then do;
    seen.add();
    output;
  end;
run;
```

### Idiom: Dorfman summary-less summarization with `find()` + `replace()`

Dorfman's Note 1 in the Hash Crash paper shows the hash as an
in-memory aggregator that sidesteps PROC SUMMARY's memory cost for
high-cardinality categorical variables: "if the only purpose is,
say, NWAY summarization, hash may do it much more economically." On
a miss, initialize the counter and `add()`; on a hit, increment and
`replace()`; on EOF, `output()` the hash to a persistent dataset.
Claims version: per-diagnosis counts, per-provider revenue rollups,
per-member claim-count histograms. (Dorfman, NESUG 2007.)

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

## Silent Pitfalls

- **Loading the driver into the hash** — a claims-scale hash OOMs
  the session when the driver is the 50M-row side. Dorfman's 2007
  paper makes this the opening caution; the rule above restates it.
  Hash is for the *small* side of the join.
- **Silent collapse on duplicate keys** — without `multidata: 'Y'`
  a duplicate key `add()` returns non-zero and the incoming row is
  dropped. Dorfman's 2015 SESUG paper documents this as the default;
  the remedy is the `multidata: 'Y'` + `find_next()` idiom above.
- **Citing an idiom to the wrong Dorfman paper** — all three Dorfman
  papers touch `find()` / `add()`. SUGI 30 (2005) is the tutorial of
  record; NESUG 2007 ("Hash Crash") adds the dedup and aggregation
  idioms; SESUG 2015 adds `multidata: 'Y'`.

## Anti-patterns (STOP signs)

- `declare hash big(dataset: 'claims');` on a 50M-row claims table —
  the hash is the wrong shape for this job; switch to PROC SQL or a
  DATA-step MERGE (see `../data-step/sql-vs-merge.md`).
- `declare hash e(dataset: 'eligibility');` on a table with multiple
  rows per member — drops every coverage span but the first; see the
  MULTIDATA idiom above.

Cross-refs: `../hash-tables/declare-and-length.md`,
`../hash-tables/find-check-rc.md`, `../hash-tables/multidata.md`,
`../hash-tables/idioms.md`.
