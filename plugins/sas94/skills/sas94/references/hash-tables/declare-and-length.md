---
title: Hash declare, define sequence, and PDV length-matching
loaded_when: '`declare hash`, `dcl hash`, `definekey`, `definedata`, `definedone`, PDV parameter-type match, `length` before hash, `if 0 then set` trick, hash lifetime across DATA steps, `h.output(dataset: ...)`.'
---

## Critical Rules

### Rule 1: The hash must be declared and loaded inside `if _N_ = 1 then do; ... end;` — or via `dataset:` — before any `set` reads the lookup column

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

`definedone()` is what locks the key / data schema and makes the hash
usable; without it, `add()`, `find()`, `check()`, and `output()` all
fail. The DATA step may still compile and run, but no row will be
added or found. Always terminate the define sequence with
`definedone()` — and check its return code in defensive code.

The snippets below highlight only the define block — for a full
self-contained DATA step (with PDV parameter-type match and a driver
`set`) see Rule 1 and the idioms file.

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

### Rule 4: Hash objects do NOT persist across DATA steps — their lifetime is exactly one step

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

## Quick Ref

| Name | Syntax | Purpose | Common mistake |
|------|--------|---------|----------------|
| `declare hash` | `declare hash h(<dataset: 'x', ordered: 'a', multidata: 'Y', hashexp: n>);` | Instantiate a hash object | Placing below `set`; PDV not type-matched |
| `dcl hash` | `dcl hash h();` | Shorthand for `declare hash` | None — pure alias |
| `definekey` | `h.definekey('k1', 'k2');` | Name the key column(s) | Forgetting to include key in `definedata` when iterator needs it |
| `definedata` | `h.definedata('v1', 'v2');` | Name the data-portion column(s) | Missing the key when iterator will walk the table |
| `definedone` | `h.definedone();` | Finalize the schema | Omitting it — every later method silently fails |
| `output` | `h.output(dataset: 'x');` | Persist hash contents to a SAS dataset | Expecting it to survive the step without `output` |
| `hashexp:` | `declare hash h(hashexp: 10);` | Bucket count = `2**hashexp` | Rarely material — defaults fine for most data |

## Silent Pitfalls

- **Parameter-type mismatch** — a `definekey('k')` where the PDV has
  not been given `k`'s type (no `length`, no `if 0 then set`) fails
  silently at run time; the hash exists but every `find()` returns a
  miss. Always type-match the PDV before `definekey`.

- **Forgotten `definedone()`** — no error at compile, but every
  `add()` / `find()` / `output()` below is a no-op. See Rule 2.

- **Expecting the hash to survive `run;`** — the hash is freed at step
  boundary. Call `h.output(dataset: ...)` before `eof` if downstream
  steps need the contents. See Rule 4.

## Anti-patterns (STOP signs)

- `declare hash` placed below `set`, outside `if _N_ = 1 then do;` —
  see Rule 1. First row reads before the hash exists.
- `definekey` / `definedata` with no trailing `definedone()` — see
  Rule 2. Silent no-op on every method.
- Second DATA step referencing a hash declared in an earlier step —
  see Rule 4. Hash is freed at `run;`.

See also `../data-step/retain-pdv.md` for the PDV / `if _N_ = 1`
control-flow pattern, and `../data-step/merge.md` for the MERGE vs
hash-lookup comparison.
