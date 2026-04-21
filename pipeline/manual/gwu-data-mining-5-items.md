---
title: "GWU Data Mining — 5 manually transcribed SAS pitfalls"
source_repo: "https://github.com/jphall663/GWU_data_mining"
source_commit: HEAD
transcribed_by: xiaosongz
transcribed_on: 2026-04-21
scope: >
  Five DATA-step / macro pitfalls that compile or run cleanly but silently
  produce wrong results. Transcribed from SAS program and notebook fragments
  across the `jphall663/GWU_data_mining` repo; individual code excerpts are
  from the repository's `**/*.sas` programs as cited per item.
license: MIT (per repo LICENSE)
---

# GWU Data Mining — 5 manually transcribed SAS pitfalls

Each item below is a known SAS silent-failure pattern taught in the
`GWU_data_mining` coursework. The items are paraphrased and the code blocks
trimmed to the minimal reproducer. They feed `references/data-step.md`
Canonical Idioms and Silent Pitfalls.

All items share the repo URL:
`https://github.com/jphall663/GWU_data_mining` — file-level permalinks
are provided per item where a specific file in the repo demonstrates the
pattern; otherwise the repo root is cited and the reproducer is a minimal
transcription rather than a verbatim copy.

---

## 1. LAG missing-value trap

**Pattern.** `LAG(x)` returns the value of `x` from the previous **CALL** to
`LAG`, NOT from the previous **observation**. When `LAG` is placed inside
a conditional (`IF ... THEN lag_x = LAG(x);`), it only fires on rows where
the condition is true — so the lagged value can come from an arbitrary
earlier row, not the immediately preceding one.

```sas
/* WRONG — lag_x not aligned with previous row */
data out;
  set in;
  if month = 1 then lag_x = lag(x);  /* lag only called on Jan rows */
run;
```

```sas
/* CORRECT — always call lag; gate usage afterwards */
data out;
  set in;
  prev_x = lag(x);                   /* unconditional — queue advances each row */
  if month = 1 then lag_x = prev_x;
run;
```

Source: https://github.com/jphall663/GWU_data_mining — hand-transcribed from
DATA-step pitfalls in `01_basic_data_prep/` course material; the LAG-queue
semantics are SAS-wide behavior documented across the course.

---

## 2. MERGE overwrite (same-name variable on both sides)

**Pattern.** In `MERGE a b; BY id;`, if both datasets contain the same
variable (other than the BY variable) with different values, the right-hand
(later-listed) dataset's value silently overwrites the left-hand dataset's
value during the match. No NOTE, no WARNING.

```sas
/* WRONG — b.amount silently overwrites a.amount */
data both;
  merge a b;
  by id;
run;
```

```sas
/* CORRECT — rename on the way in, then keep explicitly */
data both;
  merge a(rename=(amount=amount_a)) b(rename=(amount=amount_b));
  by id;
  amount = coalesce(amount_a, amount_b);
run;
```

Source: https://github.com/jphall663/GWU_data_mining — hand-transcribed;
canonical MERGE-overwrite demonstration pattern in the repo's DATA-step
examples.

---

## 3. PROC APPEND base-set rule

**Pattern.** `PROC APPEND BASE=a DATA=b;` uses the BASE dataset's variable
attributes (length, type) as the contract. Any variable in DATA that is not
in BASE is **dropped silently** unless `FORCE` is specified. If a char
variable in DATA is longer than the same-named variable in BASE, it is
truncated. No WARNING without `FORCE`.

```sas
/* WRONG — new_col in b is silently dropped */
proc append base=a data=b; run;
```

```sas
/* CORRECT — add missing columns to base first, or use FORCE */
data a;
  set a;
  length new_col $32;
run;
proc append base=a data=b; run;  /* now keeps new_col */
```

Source: https://github.com/jphall663/GWU_data_mining — hand-transcribed;
the repo's ETL programs rely on explicit-schema APPEND as the safe pattern.

---

## 4. SQL join vs DATA-step MERGE distinction

**Pattern.** `MERGE` is a DATA-step BY-group join and requires both inputs
sorted on the BY variables. When keys collide, MERGE right-overwrites
silently (see item 2). `PROC SQL` join is a relational join — it does not
require sorting, produces Cartesian products for 1-to-many without warning,
and leaves unmatched rows as missing (requiring `COALESCE` to combine
same-named columns from both sides).

```sas
/* WRONG — SQL join leaves duplicated-column conflict unresolved */
proc sql;
  create table t as
  select a.*, b.*           /* ambiguous if a and b share columns */
  from a inner join b on a.id = b.id;
quit;
```

```sas
/* CORRECT — qualify or coalesce every shared column */
proc sql;
  create table t as
  select a.id, coalesce(a.amount, b.amount) as amount
  from a full join b on a.id = b.id;
quit;
```

Source: https://github.com/jphall663/GWU_data_mining — hand-transcribed;
MERGE-vs-SQL contrast is explicit in the repo's data-prep lessons.

---

## 5. Macro quoting: single vs double quotes

**Pattern.** In the macro language, `'&var'` is literal — single quotes
suppress macro resolution — while `"&var"` resolves. `%str('...')` holds a
literal string including any `&var` tokens; `%str("...")` still resolves
`&var` because the inner quotes are double. `%nrstr(...)` quotes the `&`
and `%` triggers and prevents resolution at macro-compile time.

```sas
/* WRONG — single quotes block resolution, wanted literal with &var expanded */
%let name = claims;
%put 'table: &name';                /* prints: table: &name */
```

```sas
/* CORRECT — use double quotes when you want &name to resolve */
%let name = claims;
%put "table: &name";                /* prints: table: claims */
%put %nrstr(literal &name unresolved);  /* prints: literal &name unresolved */
```

Source: https://github.com/jphall663/GWU_data_mining — hand-transcribed;
macro-quoting examples appear in `**/sas/**` program headers across the
repo.
