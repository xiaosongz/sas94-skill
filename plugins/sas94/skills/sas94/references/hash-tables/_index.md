---
title: Hash objects reference index
loaded_when: '"hash join", "hash lookup", `declare hash`, `definekey`, `hashiter`, or any DATA-step hash-object task.'
---

## Routing table

| Atom | Load when the question involves |
|------|----------------------------------|
| `declare-and-length.md` | `declare hash`, `definekey`, `definedata`, `definedone`, PDV parameter-type match, `length` before hash, `if 0 then set` trick, hash lifetime across DATA steps |
| `find-check-rc.md` | `find()` / `check()` return codes, `rc = 0` guard, `call missing()` reset between misses, `add()` vs `replace()` semantics |
| `iteration.md` | `declare hiter`, `hi.first()` / `hi.last()` / `hi.next()` / `hi.prev()`, key-in-definedata requirement, `h.output(dataset: 'x')` persistence, `ordered:` tag |
| `multidata.md` | `multidata: 'Y'` rule, `find_next()`, one-to-many hash joins, duplicate-key handling, silent first-row-only dedup trap |
| `idioms.md` | Canonical idioms: streaming reference lookup, Dorfman dedup (`check()` + `add()`), in-memory counter/aggregator, one-to-many join |

## One-line summaries

- **declare-and-length**: the hash must be declared and loaded inside `if _N_ = 1 then do; ... end;`, and the PDV must be parameter-type-matched (via `length` or `if 0 then set lookup;`) before `definekey`. Always terminate the schema with `definedone()`. Hash lifetime is exactly one DATA step — persist via `h.output(dataset: 'x')` if downstream steps need the contents.

- **find-check-rc**: `rc = h.find();` returns 0 on a hit and non-zero on a miss; without the `if rc = 0` guard, a missed row keeps the data-portion values from the previous hit (the "silent last-retrieved-values" bug). `call missing(...)` before each `find()` is the belt-and-braces fix. `add()` fails on duplicate keys (first wins); `replace()` overwrites (last wins) — pick deliberately.

- **iteration**: a `declare hiter` walks entries in the order set by `ordered:` ('a' ascending, 'd' descending, 'n' internal). `first()` / `last()` populate key + data; `next()` / `prev()` update only the data-portion variables — so the key must appear in BOTH `definekey` AND `definedata` if you need it to surface each iteration. Memory grows linearly with loaded rowcount; a 50M-row claims hash OOMs the session.

- **multidata**: the default hash silently collapses duplicate keys to the first row. `multidata: 'Y'` plus a `do while (rc = 0); ... rc = h.find_next(); end;` loop is the one-to-many equi-join idiom. Without it, every claim matches at most one eligibility span — usually not what was meant.

- **idioms**: four canonical patterns — (1) reference-table lookup with `if 0 then set` PDV match + `dataset:` load, (2) Dorfman dedup via key-only hash + `check() ne 0` then `add()`, (3) in-memory counter via `find()` then `replace()` else `add()` with `h.output(dataset: ...)` at eof, (4) one-to-many equi-join with `multidata: 'Y'` + `find_next()`.

## Cross-references

- MERGE vs hash-lookup comparison, `if _N_ = 1 then do;` pattern: `../data-step/merge.md`, `../data-step/retain-pdv.md`.
- SQL join alternative when the lookup table does not fit in memory: see the PROC SQL reference.
- `PROC SORT NODUPKEY` as a dedup alternative to the hash-`check()` idiom: `../base-procs/proc-sort.md`.
