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

## 3. PROC APPEND variable-shape rules

**Pattern.** `PROC APPEND BASE=a DATA=b` uses BASE's variable definitions.
Without `FORCE`, any variable in DATA= that is absent from BASE= causes
the step to **fail with ERROR** — nothing is appended. With `FORCE`, the
extra variable is **dropped with a WARNING** and the step proceeds. The
silent failure mode is different: when BASE= carries a variable absent
from DATA=, appended rows get missing values in that column, no
diagnostic — easy to miss when BASE= has been recently extended. Char
length mismatches (DATA's var wider than BASE's) produce truncation with
a NOTE.

```sas
/* WRONG — DATA has a column absent from BASE; step errors without FORCE */
proc append base=claims data=claims_new;
run;
/* ERROR: Variable new_flag in DATA set not in BASE set. No appending done. */

/* Subtler silent mode: BASE has a column absent from DATA */
proc append base=claims_v2 data=claims_v1;   /* v2 added new_flag; v1 lacks it */
run;
/* Step succeeds; new_flag is missing for every v1 row — no WARNING. */
```

```sas
/* CORRECT — align DATA columns to BASE before appending, or use FORCE knowingly */
proc append base=claims data=claims_new force;   /* drops new-in-DATA vars w/ WARNING */
run;

/* or: explicitly reshape DATA to match BASE */
data claims_aligned;
  set claims_new;
  keep patient_id claim_dt cost;   /* whatever BASE=claims has */
run;
proc append base=claims data=claims_aligned;    /* no FORCE needed */
run;
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

## 5. Macro resolution and quote semantics

**Pattern.** In DATA/PROC step string literals, single quotes keep `&var`
literal while double quotes resolve it — this is the real single-vs-double
rule. In macro-context statements (`%put`, `%let`, `%if`), the macro
processor scans for `&` and `%` triggers *before* the statement receives
its argument, so quote type does not suppress resolution — the common
misconception that `%put 'table: &var';` holds `&var` literal is wrong.
Use `%nrstr(...)` or `%str(%&...)` to mask triggers in macro context.

```sas
/* CORRECT — single-quoted DATA-step literal: &name is not resolved */
%let name = claims;
data _null_;
  x = 'table: &name';
  put x;          /* writes: table: &name */
run;

/* CORRECT — double-quoted DATA-step literal: &name resolves */
data _null_;
  x = "table: &name";
  put x;          /* writes: table: claims */
run;

/* CORRECT — macro-context masking requires %nrstr, not quotes */
%put %nrstr(literal &name is unresolved);     /* writes: literal &name is unresolved */
```

```sas
/* WRONG — single quotes in %put do NOT suppress resolution */
%let name = claims;
%put 'table: &name';   /* writes: table: claims — quotes are literal output chars */
```

Source: https://github.com/jphall663/GWU_data_mining — hand-transcribed;
macro-quoting examples appear in `**/sas/**` program headers across the
repo.
