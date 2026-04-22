---
title: Hash objects reference
scope: '`declare hash`, `definekey` / `definedata` / `definedone`, `find` / `check` / `add` / `replace`, and hash iterators (`hiter`).'
loaded_when: '"hash join", "hash lookup", `declare hash`, `definekey`, `hashiter`, or any DATA-step hash-object task.'
last_reviewed: 2026-04-22
reviewer: xiaosongz
---

## Overview

The DATA-step hash object is a run-time, memory-resident associative
array introduced in SAS 9 via the Data Step Component Interface. Unlike
`MERGE` or PROC SQL joins, a hash lookup is O(1) expected time and does
not require pre-sorting the lookup table — a natural fit for
claims-work patterns such as "attach the ICD-10 description table to
every claim row" or "flag every pat-id/service-date pair already seen
this run." The trade-off is memory: the whole lookup table loads into
RAM in one shot, so a 50M-row claims extract will happily consume every
byte the SAS session is allowed.

Almost every hash-object bug reduces to one of four root causes: (1)
the `declare` / `defineX` sequence executes on a row where the PDV does
not yet hold the key's type / length, so parameter type matching
silently fails; (2) the programmer forgets `definedone()`, and SAS
rejects every subsequent method call; (3) the `find()` return code is
not checked, so on a miss the PDV keeps whatever the last successful
`find()` wrote ("silent last-retrieved-values," which Dorfman flags as
the central DATA-step hash pitfall); (4) duplicate keys are loaded
without `multidata: 'Y'`, so only the first entry per key survives.
This file encodes the rules from the SAS Language Reference: Processing
Guide (lepg) "Hash Table Merging" section and the three Paul Dorfman
lexjansen papers — SUGI 30 (2005), NESUG 2007, and SESUG 2015 — on
hash programming and duplicate keys.

See also `data-step.md` for the MERGE vs hash-lookup comparison and
`proc-sql.md` for the SQL join alternative when the lookup table does
not fit in memory.

## Contents

- [Critical Rules](#critical-rules)
- [Canonical Idioms](#canonical-idioms)
- [Function / Statement Quick Ref](#function--statement-quick-ref)
- [Silent Pitfalls](#silent-pitfalls)
- [Anti-patterns (STOP signs)](#anti-patterns-stop-signs)
- [See Also](#see-also)

## Critical Rules

### Rule 1: The hash must be declared and loaded inside `if _N_ = 1 then do; ... end;` — or via `dataset:` — before any `set` reads the lookup column

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lepg&docsetTarget=titlepage.htm

The hash object is created and populated at run time, not compile
time. If you put `declare hash ...` below the `set large;`, the first
observation reads its key before the hash exists, and `find()` returns
a miss for row 1 regardless of the lookup table's contents. The
canonical structure is: (1) parameter-type-match the PDV via a
`length` statement or a no-op `if 0 then set lookup;`, (2) declare +
populate + `definedone()` inside `if _N_ = 1 then do; ... end;`, (3)
then `set` the large driver and call `find()`.

```sas
/* CORRECT - hash built on first iteration, then driver set reads */
data claims_plus_desc;
  length dx_desc $60;
  if _N_ = 1 then do;
    declare hash h(dataset: 'icd10_ref');
    h.definekey('dx_code');
    h.definedata('dx_desc');
    h.definedone();
    call missing(dx_desc);  /* silences uninitialized NOTE */
  end;
  set claims;
  if h.find() = 0;  /* keep only matched claims */
run;
```

```sas
/* WRONG - declare runs every iteration; SAS errors on 2nd row because
   the hash already exists, and the PDV columns have not been
   parameter-type-matched before definekey. */
data claims_plus_desc;
  set claims;
  declare hash h(dataset: 'icd10_ref');
  h.definekey('dx_code');
  h.definedata('dx_desc');
  h.definedone();
  if h.find() = 0;
run;
```

### Rule 2: Omitting `definedone()` is a silent error — every subsequent method call fails

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lepg&docsetTarget=titlepage.htm

`definedone()` is what locks the key / data schema and makes the hash
usable; without it, `add()`, `find()`, `check()`, and `output()` all
fail. The DATA step may still compile and run, but no row will be
added or found. Always terminate the define sequence with
`definedone()` — and check its return code in defensive code.

The snippets below highlight only the define block — for a full
self-contained DATA step (with PDV parameter-type match and a driver
`set`) see Rule 1 and the "Reference-table lookup" idiom below.

```sas
/* CORRECT - definedone() terminates the schema (fragment; see Rule 1 for full DATA step) */
if _N_ = 1 then do;
  length pat_id $20 plan_type $10;  /* PDV type-match for definekey / definedata */
  declare hash h();
  h.definekey('pat_id');
  h.definedata('pat_id', 'plan_type');
  h.definedone();
end;
```

```sas
/* WRONG - no definedone(); every h.add() / h.find() below silently fails (fragment) */
if _N_ = 1 then do;
  length pat_id $20 plan_type $10;
  declare hash h();
  h.definekey('pat_id');
  h.definedata('pat_id', 'plan_type');
end;
```

### Rule 3: Always check the `find()` return code — ignoring it means silent use of the last-retrieved values

Source: https://support.sas.com/resources/papers/proceedings/proceedings/sugi30/236-30.pdf

`rc = h.find();` returns 0 on a hit and non-zero on a miss. When the
call hits, SAS copies the data-portion values into the PDV; when it
misses, it leaves the PDV unchanged. If you forget the `if rc = 0`
guard, a missed row keeps the data-portion values from the previous
hit — the most common "my lookup is 100% matched!" bug. Either test
`rc` before using the retrieved columns, or call `call missing(...)`
after every miss.

```sas
/* CORRECT - explicit return-code branch */
set claims;
call missing(plan_type);  /* reset before each lookup */
if h.find() = 0 then plan_hit = 1;
else plan_hit = 0;
```

```sas
/* WRONG - plan_type keeps the previous row's value on a miss */
set claims;
rc = h.find();
/* plan_type used below without checking rc - silent last-value bug */
output;
```

### Rule 4: Hash objects do NOT persist across DATA steps — their lifetime is exactly one step

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lepg&docsetTarget=titlepage.htm

Every `declare hash` is scoped to the DATA step that creates it; when
the step's `run;` fires, the hash and its memory are freed. If you
need the contents downstream, call `h.output(dataset: 'work.x');` to
persist them as a SAS dataset before the step ends. A common bug is
declaring a hash in one `data _null_` and expecting a later DATA step
to reuse it — it won't; the second step sees no hash at all.

```sas
/* CORRECT - persist the hash contents before the step ends */
data _null_;
  if _N_ = 1 then do;
    declare hash counts();
    counts.definekey('dx_code');
    counts.definedata('dx_code', 'n');
    counts.definedone();
  end;
  set claims end=eof;
  /* ... populate counts via find()/replace() ... */
  if eof then counts.output(dataset: 'dx_counts');
run;

/* downstream step reads the PERSISTED dataset, not the freed hash */
data report;
  set dx_counts;
run;
```

```sas
/* WRONG - second DATA step references counts, which no longer exists */
data _null_;
  if _N_ = 1 then do;
    declare hash counts();
    counts.definekey('dx_code');
    counts.definedata('n');
    counts.definedone();
  end;
  set claims;
  /* ... */
run;

data report;
  /* no declare; counts is undefined here */
  rc = counts.find();  /* run-time error: "Object 'counts' is not defined" */
run;
```

### Rule 5: Without `multidata: 'Y'`, only the first row per key loads — silent dedup on the key column

Source: https://www.lexjansen.com/sesug/2015/94_Final_PDF.pdf

When a hash table is loaded from a dataset (`dataset:` tag) and two
rows share the same key, the default behavior keeps the first and
silently ignores the rest — as if `add()` were used, which returns a
non-zero code on a duplicate. For lookups where the key is supposed
to be unique (ICD-10 codes, member IDs) this is the right behavior.
For one-to-many joins (claims → all eligibility spans), you need
`multidata: 'Y'` plus `find_next()` to harvest every match.

```sas
/* CORRECT - multidata allows duplicate keys; find_next() harvests them */
data claim_elig;
  if _N_ = 1 then do;
    if 0 then set eligibility;
    declare hash elig(dataset: 'eligibility', multidata: 'Y');
    elig.definekey('member_id');
    elig.definedata('plan_id', 'eff_dt', 'term_dt');
    elig.definedone();
  end;
  set claims;
  rc = elig.find();
  do while (rc = 0);
    output;
    rc = elig.find_next();
  end;
run;
```

```sas
/* WRONG - duplicate member_id rows silently collapse to the first one */
if _N_ = 1 then do;
  if 0 then set eligibility;
  declare hash elig(dataset: 'eligibility');  /* no multidata tag */
  elig.definekey('member_id');
  elig.definedata('plan_id', 'eff_dt', 'term_dt');
  elig.definedone();
end;
set claims;
if elig.find() = 0 then output;
/* every claim matches at most ONE eligibility span — usually not what was meant */
```

### Rule 6: `add()` fails on a duplicate key; `replace()` overwrites — pick deliberately

Source: https://support.sas.com/resources/papers/proceedings/proceedings/sugi30/236-30.pdf

With the default (non-multidata) hash, `add()` returns a non-zero code
and discards the incoming row when the key already exists; `replace()`
silently overwrites the existing row's data-portion values with the
new ones. Loading a lookup table row-by-row via `add()` therefore
keeps the **first** instance per key; via `replace()`, the **last**.
If the lookup source has duplicates and you need the last version,
use `replace()`; if you need the first, use `add()`. The `dataset:`
tag is equivalent to an `add()` loop — it keeps the first.

Snippets below show only the load loop — a self-contained step would
wrap these in `data _null_; if _N_ = 1 then do; declare hash h(); ...
h.definedone(); end;` as in Rule 1.

```sas
/* CORRECT - replace() keeps the most-recent row per key (fragment; see Rule 1) */
do until (eof);
  set ref_updates end=eof;
  h.replace();
end;
```

```sas
/* WRONG - add() silently discards the "newer" row when the key is a dup (fragment) */
do until (eof);
  set ref_updates end=eof;
  h.add();  /* first row wins; later updates lost */
end;
```

### Rule 7: The hash iterator (`hiter`) traverses in order — but `next()`/`prev()` only updates data-portion variables, NOT the key

Source: https://support.sas.com/resources/papers/proceedings/proceedings/sugi30/236-30.pdf

A `declare hiter` binds an iterator to a hash and makes entries
accessible in the order defined by `ordered:` ('a' ascending, 'd'
descending, 'n' internal). `hi.first()` and `hi.last()` populate both
the key and the data-portion host variables; subsequent `hi.next()` /
`hi.prev()` calls update only the data-portion variables. If you need
the key to surface each iteration, include it in the `definedata`
list as well as `definekey`. A common bug: the first / last key
prints correctly but the middle rows carry the wrong key.

```sas
/* CORRECT - key variable listed in both definekey AND definedata */
if _N_ = 1 then do;
  if 0 then set claims;
  declare hash h(dataset: 'claims', ordered: 'a');
  declare hiter hi('h');
  h.definekey('dx_code');
  h.definedata('dx_code', 'n_claims');  /* key repeated here */
  h.definedone();
end;
rc = hi.first();
do while (rc = 0);
  put dx_code= n_claims=;
  rc = hi.next();
end;
```

```sas
/* WRONG - dx_code absent from definedata; only first() updates it,
   every next() row carries the first row's key (fragment; see Rule 1 for
   full wrapping DATA step with `if 0 then set` PDV type-match). */
h.definekey('dx_code');
h.definedata('n_claims');  /* dx_code missing */
```

### Rule 8: Hash memory grows with the loaded rowcount — claims-scale lookups can OOM the session

Source: https://www.lexjansen.com/nesug/nesug07/ff/ff03.pdf

The hash object holds every key + data-portion row in memory for the
life of the DATA step. For a 50M-row claims table with a 30-byte key
and a 500-byte data portion, that is roughly 25 GB — most likely more
than the session's MEMSIZE. Use hash for the **small** side of a
join (the lookup / reference table), not the large side. When both
sides are large, switch to a SQL join, a DATA-step MERGE on sorted
data, or a SORT + BY-group MERGE.

```sas
/* CORRECT - small reference table in hash, large driver streams via set */
if _N_ = 1 then do;
  declare hash ref(dataset: 'icd10_ref');  /* ~70k rows, fits easily */
  ref.definekey('dx_code');
  ref.definedata('dx_desc', 'chapter');
  ref.definedone();
end;
set claims;  /* 50M rows - streamed, not loaded */
rc = ref.find();
```

```sas
/* WRONG - loading the 50M-row claims table into the hash OOMs the session */
if _N_ = 1 then do;
  declare hash big(dataset: 'claims');  /* attempts to load 50M rows into RAM */
  big.definekey('claim_id');
  big.definedata('paid_amt', 'service_dt', 'dx_code');
  big.definedone();
end;
set icd10_ref;
rc = big.find();
```

## Canonical Idioms

### Idiom: Reference-table lookup — attach ICD-10 description to every claim row

Source: https://support.sas.com/resources/papers/proceedings/proceedings/sugi30/236-30.pdf

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

Source: https://www.lexjansen.com/nesug/nesug07/ff/ff03.pdf

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

Source: https://support.sas.com/resources/papers/proceedings/proceedings/sugi30/236-30.pdf

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

Source: https://www.lexjansen.com/sesug/2015/94_Final_PDF.pdf

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

## Function / Statement Quick Ref

| Name | Syntax | Purpose | Common mistake | Doc URL |
|------|--------|---------|----------------|---------|
| `declare hash` | `declare hash h(<dataset: 'x', ordered: 'a', multidata: 'Y', hashexp: n>);` | Instantiate a hash object | Placing below `set`; PDV not type-matched | [DECLARE Statement, Hash Object](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lepg&docsetTarget=titlepage.htm) |
| `dcl hash` | `dcl hash h();` | Shorthand for `declare hash` | None — pure alias | [DECLARE Statement, Hash Object](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lepg&docsetTarget=titlepage.htm) |
| `definekey` | `h.definekey('k1', 'k2');` | Name the key column(s) | Forgetting to include key in `definedata` when iterator needs it | [DEFINEKEY Method (Hash Object)](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lepg&docsetTarget=titlepage.htm) |
| `definedata` | `h.definedata('v1', 'v2');` | Name the data-portion column(s) | Missing the key when iterator will walk the table | [DEFINEDATA Method (Hash Object)](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lepg&docsetTarget=titlepage.htm) |
| `definedone` | `h.definedone();` | Finalize the schema | Omitting it — every later method silently fails | [DEFINEDONE Method (Hash Object)](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lepg&docsetTarget=titlepage.htm) |
| `find` | `rc = h.find();` | Retrieve row for current key; 0 = hit | Not checking `rc` → last-retrieved-values bug | [FIND Method (Hash Object)](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lepg&docsetTarget=titlepage.htm) |
| `find_next` | `rc = h.find_next();` | Next duplicate for same key (requires `multidata: 'Y'`) | Calling without `multidata: 'Y'` | [FIND_NEXT Method (Hash Object)](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lepg&docsetTarget=titlepage.htm) |
| `check` | `rc = h.check();` | Test if key exists without retrieving data | Confusing with `find` — check doesn't populate PDV | [CHECK Method (Hash Object)](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lepg&docsetTarget=titlepage.htm) |
| `add` | `rc = h.add();` | Insert row; fails on duplicate key | Wanting "upsert" semantics — use `replace` | [ADD Method (Hash Object)](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lepg&docsetTarget=titlepage.htm) |
| `replace` | `rc = h.replace();` | Insert or overwrite existing key | Losing the first value when you wanted first-wins | [REPLACE Method (Hash Object)](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lepg&docsetTarget=titlepage.htm) |
| `remove` | `rc = h.remove();` | Delete current key's entry | Calling without a prior `find` / `check` | [REMOVE Method (Hash Object)](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lepg&docsetTarget=titlepage.htm) |
| `output` | `h.output(dataset: 'x');` | Persist hash contents to a SAS dataset | Expecting it to survive the step without `output` | [OUTPUT Method (Hash Object)](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lepg&docsetTarget=titlepage.htm) |
| `declare hiter` | `declare hiter hi('h');` | Bind iterator to a hash | Passing hash name unquoted; must be a string | [DECLARE Statement, Hash Iterator](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lepg&docsetTarget=titlepage.htm) |
| `hi.first` / `hi.last` | `rc = hi.first();` | Move to ordered first / last entry | Requires `ordered:` on the hash to be meaningful | [Hash Iterator FIRST/LAST Methods](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lepg&docsetTarget=titlepage.htm) |
| `hi.next` / `hi.prev` | `rc = hi.next();` | Move to next / prev entry | Updates data-portion only, not key (Rule 7) | [Hash Iterator NEXT/PREV Methods](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lepg&docsetTarget=titlepage.htm) |
| `multidata: 'Y'` | `declare hash h(multidata: 'Y');` | Accept duplicate keys | Omitting it → silent dedup to first row per key | [MULTIDATA Argument Tag (Hash)](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lepg&docsetTarget=titlepage.htm) |
| `ordered:` | `declare hash h(ordered: 'a');` | Maintain key order | Passing a numeric literal → runtime error | [ORDERED Argument Tag (Hash)](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lepg&docsetTarget=titlepage.htm) |
| `hashexp:` | `declare hash h(hashexp: 10);` | Bucket count = `2**hashexp` | Rarely material — defaults fine for most data | [HASHEXP Argument Tag (Hash)](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lepg&docsetTarget=titlepage.htm) |

## Silent Pitfalls

- **Missing `rc` check on `find()`** — the PDV retains the previous
  hit's values on a miss, so the output looks 100% matched when in
  fact half the rows are false positives. See Rule 3. Always branch
  on `rc` or `call missing()` before every `find()`.
  Source: https://support.sas.com/resources/papers/proceedings/proceedings/sugi30/236-30.pdf

- **Parameter-type mismatch** — a `definekey('k')` where the PDV has
  not been given `k`'s type (no `length`, no `if 0 then set`) fails
  silently at run time; the hash exists but every `find()` returns a
  miss. Always type-match the PDV before `definekey`.
  Source: https://support.sas.com/resources/papers/proceedings/proceedings/sugi30/236-30.pdf

- **Forgotten `definedone()`** — no error at compile, but every
  `add()` / `find()` / `output()` below is a no-op. See Rule 2.
  Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lepg&docsetTarget=titlepage.htm

- **Duplicate keys silently collapse without `multidata: 'Y'`** —
  loading a table where the key is not unique keeps only the first
  row per key; later rows are dropped with a non-zero `add()` return
  code that most code ignores. See Rules 5 and 6.
  Source: https://www.lexjansen.com/sesug/2015/94_Final_PDF.pdf

- **Hash iterator middle rows carry stale key** — `hi.next()` only
  updates data-portion variables; omitting the key from `definedata`
  leaves `first()`-set key frozen across the iteration. See Rule 7.
  Source: https://support.sas.com/resources/papers/proceedings/proceedings/sugi30/236-30.pdf

- **OOM on claims-scale hash** — a hash sized to the full claims
  table exhausts MEMSIZE. Hash is for the small side only; see
  Rule 8 and switch to SQL / MERGE when both sides are large.
  Source: https://www.lexjansen.com/nesug/nesug07/ff/ff03.pdf

## Anti-patterns (STOP signs)

**STOP** when you see any of the following — the step compiles and
runs, but the results are almost certainly not what the author meant:

- `declare hash` placed below `set`, outside `if _N_ = 1 then do;` —
  see Rule 1. First row reads before the hash exists.
- `definekey` / `definedata` with no trailing `definedone()` — see
  Rule 2. Silent no-op on every method.
- `rc = h.find();` with no `if rc = 0` guard — see Rule 3.
  Last-retrieved-values bug.
- Second DATA step referencing a hash declared in an earlier step —
  see Rule 4. Hash is freed at `run;`.
- `declare hash h(dataset: 'x');` where `x` has duplicate keys and
  the code expects them all to load — see Rule 5. Add
  `multidata: 'Y'`.
- Loading the large side of a join into the hash — see Rule 8.
  Memory grows linearly with rowcount.

## See Also

- [data-step.md](data-step.md) — MERGE vs hash-lookup comparison;
  `if _N_ = 1 then do;` pattern under DATA-step control flow.
- [proc-sql.md](proc-sql.md) — SQL join alternative when the lookup
  table does not fit in memory.
- [base-procs.md](base-procs.md) — `PROC SORT NODUPKEY` as a
  dedup alternative to the hash-`check()` idiom.
- [idioms-from-lexjansen.md](idioms-from-lexjansen.md) — deeper hash
  treatments from Dorfman and other authors.
- [SAS Language Reference: Processing Guide](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lepg&docsetTarget=titlepage.htm)
- [Dorfman (2005) — Data Step Hash Objects as Programming Tools](https://support.sas.com/resources/papers/proceedings/proceedings/sugi30/236-30.pdf)
- [Dorfman (2007) — Hash Crash and Beyond](https://www.lexjansen.com/nesug/nesug07/ff/ff03.pdf)
- [Dorfman (2015) — Using the SAS Hash Object with Duplicate Key Entries](https://www.lexjansen.com/sesug/2015/94_Final_PDF.pdf)
