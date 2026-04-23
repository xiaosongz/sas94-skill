---
title: Hash iterator (hiter), ordering, and memory footprint
loaded_when: '`declare hiter`, `hi.first()`, `hi.last()`, `hi.next()`, `hi.prev()`, `ordered:` tag, hash iteration order, `h.output(dataset: ...)` from iterator, OOM on claims-scale hash, `hashexp:` tuning.'
---

## Critical Rules

### Rule 7: The hash iterator (`hiter`) traverses in order — but `next()`/`prev()` only updates data-portion variables, NOT the key

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
   every next() row carries the first row's key (fragment; see the
   declare-and-length atom for the full wrapping DATA step with
   `if 0 then set` PDV type-match). */
h.definekey('dx_code');
h.definedata('n_claims');  /* dx_code missing */
```

### Rule 8: Hash memory grows with the loaded rowcount — claims-scale lookups can OOM the session

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

## Quick Ref

| Name | Syntax | Purpose | Common mistake |
|------|--------|---------|----------------|
| `declare hiter` | `declare hiter hi('h');` | Bind iterator to a hash | Passing hash name unquoted; must be a string |
| `hi.first` / `hi.last` | `rc = hi.first();` | Move to ordered first / last entry | Requires `ordered:` on the hash to be meaningful |
| `hi.next` / `hi.prev` | `rc = hi.next();` | Move to next / prev entry | Updates data-portion only, not key (Rule 7) |
| `ordered:` | `declare hash h(ordered: 'a');` | Maintain key order | Passing a numeric literal → runtime error |

## Silent Pitfalls

- **Hash iterator middle rows carry stale key** — `hi.next()` only
  updates data-portion variables; omitting the key from `definedata`
  leaves `first()`-set key frozen across the iteration. See Rule 7.

- **OOM on claims-scale hash** — a hash sized to the full claims
  table exhausts MEMSIZE. Hash is for the small side only; see
  Rule 8 and switch to SQL / MERGE when both sides are large.

- **`ordered:` without an iterator** — setting `ordered: 'a'` on a
  hash that is only queried via `find()` buys nothing and adds load
  cost. The ordering is only observable through `hiter`.

## Anti-patterns (STOP signs)

- `declare hiter hi(h);` passing the hash name as a bare identifier —
  it must be a quoted string (`'h'`). Compile error.
- Loading the large side of a join into the hash — see Rule 8.
  Memory grows linearly with rowcount.
- Key absent from `definedata` when a `hiter` walks the table — see
  Rule 7. Middle-row keys silently freeze on the first entry.
