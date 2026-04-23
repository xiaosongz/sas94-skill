---
title: Hash multidata duplicate-key handling and find_next
loaded_when: '`multidata: ''Y''`, `find_next()`, one-to-many hash join, duplicate keys in hash, silent first-row-only dedup, eligibility span lookup.'
---

## Critical Rules

### Rule 5: Without `multidata: 'Y'`, only the first row per key loads — silent dedup on the key column

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

## Quick Ref

| Name | Syntax | Purpose | Common mistake |
|------|--------|---------|----------------|
| `multidata: 'Y'` | `declare hash h(multidata: 'Y');` | Accept duplicate keys | Omitting it → silent dedup to first row per key |
| `find_next` | `rc = h.find_next();` | Next duplicate for same key (requires `multidata: 'Y'`) | Calling without `multidata: 'Y'` |

## Silent Pitfalls

- **Duplicate keys silently collapse without `multidata: 'Y'`** —
  loading a table where the key is not unique keeps only the first
  row per key; later rows are dropped with a non-zero `add()` return
  code that most code ignores. See Rule 5 (and pair with the
  `add()` vs `replace()` distinction in the find-check-rc atom).

- **`find_next()` called without `multidata: 'Y'`** — the method
  returns non-zero immediately; the `do while` loop runs zero extra
  iterations and the step silently behaves as if there were only one
  match per key.

- **Eligibility date filter inside vs outside the loop** — apply
  date-range tests (`eff_dt <= service_dt <= term_dt`) INSIDE the
  `do while (rc = 0)` loop so each span is tested; moving the test
  outside the loop tests only the last span returned by
  `find_next()`.

## Anti-patterns (STOP signs)

- `declare hash h(dataset: 'x');` where `x` has duplicate keys and
  the code expects them all to load — see Rule 5. Add
  `multidata: 'Y'`.
- `find_next()` used on a hash without `multidata: 'Y'` — silent
  one-match-per-key behavior.
- Forgetting to re-check `rc` inside the `do while` loop — the loop
  only terminates when `rc ne 0`; using the wrong variable name
  (shadowing `rc` with something else) makes it infinite.
