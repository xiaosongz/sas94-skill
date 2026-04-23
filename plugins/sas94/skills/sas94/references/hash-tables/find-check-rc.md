---
title: Hash find / check return-code guard and add vs replace semantics
loaded_when: '`find()`, `check()`, `add()`, `replace()`, `remove()`, hash return code, `rc = 0` guard, `call missing()` reset, silent last-retrieved-values bug, upsert semantics.'
---

## Critical Rules

### Rule 3: Always check the `find()` return code — ignoring it means silent use of the last-retrieved values

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

### Rule 6: `add()` fails on a duplicate key; `replace()` overwrites — pick deliberately

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
h.definedone(); end;` as in the declare-and-length atom.

```sas
/* CORRECT - replace() keeps the most-recent row per key (fragment) */
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

## Quick Ref

| Name | Syntax | Purpose | Common mistake |
|------|--------|---------|----------------|
| `find` | `rc = h.find();` | Retrieve row for current key; 0 = hit | Not checking `rc` — last-retrieved-values bug |
| `check` | `rc = h.check();` | Test if key exists without retrieving data | Confusing with `find` — check doesn't populate PDV |
| `add` | `rc = h.add();` | Insert row; fails on duplicate key | Wanting "upsert" semantics — use `replace` |
| `replace` | `rc = h.replace();` | Insert or overwrite existing key | Losing the first value when you wanted first-wins |
| `remove` | `rc = h.remove();` | Delete current key's entry | Calling without a prior `find` / `check` |

## Silent Pitfalls

- **Missing `rc` check on `find()`** — the PDV retains the previous
  hit's values on a miss, so the output looks 100% matched when in
  fact half the rows are false positives. See Rule 3. Always branch
  on `rc` or `call missing()` before every `find()`.

- **`add()` returning non-zero on a dup is not an error** — the row is
  silently discarded and execution continues. If you need to know,
  assign `rc = h.add();` and branch on it explicitly.

- **`check()` confused with `find()`** — `check()` tests presence
  without touching the PDV; use it in dedup idioms. `find()` hydrates
  the PDV on a hit. Swapping them either drops wanted updates or
  wastes work retrieving data you never use.

## Anti-patterns (STOP signs)

- `rc = h.find();` with no `if rc = 0` guard — see Rule 3.
  Last-retrieved-values bug.
- Using `h.add()` in an "upsert" path when duplicates carry updates —
  the update silently loses; use `h.replace()`. See Rule 6.
- Assuming `dataset:` preserves duplicates — the tag is an `add()`
  loop and keeps the first row per key only (see the multidata atom
  for the fix).
