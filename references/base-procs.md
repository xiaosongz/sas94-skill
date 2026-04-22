---
title: Base SAS procedures reference
scope: PROC FREQ, MEANS, UNIVARIATE, SORT, TRANSPOSE, REPORT, PRINT — options, output-dataset idioms, and the silent-failure modes that separate the defaults from what analysts usually mean.
loaded_when: '"PROC FREQ", "PROC MEANS", "PROC UNIVARIATE", "PROC SORT", "PROC TRANSPOSE", "PROC REPORT", "PROC PRINT", "NODUPKEY", "OUTPUT OUT=", or any descriptive-statistics / tabulation / reshape task.'
last_reviewed: 2026-04-22
reviewer: xiaosongz
---

## Overview

The seven procedures in this file — `FREQ`, `MEANS`, `UNIVARIATE`,
`SORT`, `TRANSPOSE`, `REPORT`, `PRINT` — cover 90% of the "count
something, summarize something, reshape something, show something"
surface area of Base SAS. They also share a stylistic quirk: each one
has a **default that does something surprising** at least once —
`PROC FREQ` drops missing from the cross-tab, `PROC MEANS` prints
before you asked, `PROC SORT` without `OUT=` silently replaces the
input, `PROC TRANSPOSE` with no `VAR` transposes every numeric in the
dataset. That list of defaults is the shape of this file.

This file encodes the usage rules from the Base SAS Procedures Guide
(SORT, MEANS, TRANSPOSE, REPORT, PRINT) and the SAS/STAT User's Guide
(FREQ, UNIVARIATE). Every rule and idiom has a code example built from
the procedure-reference docs; the examples are claims-data-flavored
because that is what the caller will most often be writing.

For statistical-modeling procs (REG, GLM, LOGISTIC, GLIMMIX,
MIXED, ...) see `stat-procs.md`; for PROC SQL see `proc-sql.md`; for
formats / informats see `formats-informats.md`.

## Contents

- [Critical Rules](#critical-rules)
- [Canonical Idioms](#canonical-idioms)
- [Function / Statement Quick Ref](#function--statement-quick-ref)
- [Silent Pitfalls](#silent-pitfalls)
- [Anti-patterns (STOP signs)](#anti-patterns-stop-signs)
- [See Also](#see-also)

## Critical Rules

### Rule 1: `PROC FREQ TABLES a*b;` drops rows with missing in `a` or `b` by default — add `/ MISSING` to count them

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=proc&docsetTarget=titlepage.htm

The default `TABLES` behavior excludes observations with a missing
value on any table variable from both the cell counts and the
percent-of-total denominator. For claims-data prevalence calculations
this silently understates the denominator. Add `/ MISSING` to treat
missing as a category, or `/ MISSPRINT` to display (but not count)
missings.

```sas
/* CORRECT - explicit: missing counted as a category */
proc freq data=claims;
  tables dx_code * plan_type / missing;
run;
```

```sas
/* WRONG - silently drops claims with missing plan_type from denominator */
proc freq data=claims;
  tables dx_code * plan_type;
run;
```

### Rule 2: `PROC MEANS` prints by default — use `NOPRINT` when you only want `OUTPUT OUT=`

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=proc&docsetTarget=titlepage.htm

A bare `proc means data=claims; ... output out=summary ... ; run;` writes
the OUTPUT dataset AND pollutes the `.lst` / ODS destination with the
default print. In batch or long pipelines this is minor; in generated
QA reports it is an unwanted section. Add `NOPRINT` on the PROC MEANS
statement.

```sas
/* CORRECT - OUTPUT dataset only, no printed table */
proc means data=claims noprint;
  class member_id;
  var paid_amt;
  output out=claims_by_member(drop=_type_ _freq_)
    sum=total_paid n=n_claims;
run;
```

```sas
/* WRONG - produces both the dataset AND a printed table */
proc means data=claims;
  class member_id;
  var paid_amt;
  output out=claims_by_member sum=total_paid n=n_claims;
run;
```

### Rule 3: `PROC SORT NODUPKEY` dedups on BY vars only — `NODUPRECS` dedups on the full row

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=proc&docsetTarget=titlepage.htm

`NODUPKEY` keeps the first observation per `BY` group and drops the
rest — even if the other columns differ. `NODUPRECS` only drops an
observation when **every column** equals the adjacent one. Mixing them
up is a common "where did my data go?" source; use `DUPOUT=` to catch
the dropped rows for audit.

```sas
/* CORRECT - deliberate: one row per member_id, log dropped dups */
proc sort data=claims out=claims_one_per_member
          nodupkey dupout=claims_dupes;
  by member_id;
run;
```

```sas
/* WRONG - expects full-row dedup but NODUPKEY keeps only one per member_id */
proc sort data=claims out=claims_dedup nodupkey;
  by member_id;
run;
/* claims with the same member_id but different service_dt → all but first lost */
```

### Rule 4: `PROC SORT` without `OUT=` **replaces** the input dataset in place

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=proc&docsetTarget=titlepage.htm

`proc sort data=claims; by member_id; run;` overwrites `claims` with
the sorted version. In an interactive session this is fine; in a
pipeline it destroys the original ordering (which may have been
meaningful — file-order from an SFTP drop, for instance). Always
specify `OUT=` unless the in-place sort is deliberate.

```sas
/* CORRECT - out= preserves the input */
proc sort data=claims out=claims_sorted;
  by member_id service_dt;
run;
```

```sas
/* WRONG - silently overwrites work.claims */
proc sort data=claims;
  by member_id service_dt;
run;
```

### Rule 5: `PROC TRANSPOSE` with no `VAR` transposes every numeric variable — and silently drops every character

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=proc&docsetTarget=titlepage.htm

With no `VAR` statement, PROC TRANSPOSE transposes the `_NUMERIC_`
variables (excluding BY / ID / COPY vars) and writes no warning about
any character variables it skipped. For mixed-type input datasets
always specify `VAR` explicitly — both to document intent and to
surface a misspelled column name as a syntax error.

```sas
/* CORRECT - explicit VAR list */
proc transpose data=claims_long out=claims_wide prefix=paid_;
  by member_id;
  id visit_seq;
  var paid_amt;
run;
```

```sas
/* WRONG - no VAR; every numeric gets transposed, no warning about dropped chars */
proc transpose data=claims_long out=claims_wide prefix=v_;
  by member_id;
  id visit_seq;
run;
```

### Rule 6: `PROC REPORT DEFINE` type determines aggregation — `DISPLAY` / `ANALYSIS` / `GROUP` / `ORDER` are not interchangeable

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=proc&docsetTarget=titlepage.htm

`DISPLAY` shows row-level values; `ANALYSIS` computes an aggregation
(`sum`, `mean`, etc. via the trailing keyword); `GROUP` collapses
rows with equal values into one; `ORDER` sorts without collapsing.
A common bug: declaring a key column as `DISPLAY` when you meant
`GROUP` — the report shows duplicate-key rows instead of summarizing.

```sas
/* CORRECT - member_id is the grouping; paid_amt is the analysis */
proc report data=claims nowd;
  column member_id paid_amt n_claims;
  define member_id / group 'Member ID';
  define paid_amt  / analysis sum format=dollar12.2 'Total Paid';
  define n_claims  / analysis n 'Claim Count';
run;
```

```sas
/* WRONG - DISPLAY keeps every row; report has one row per claim, not per member */
proc report data=claims nowd;
  column member_id paid_amt;
  define member_id / display;
  define paid_amt  / display;
run;
```

### Rule 7: `PROC UNIVARIATE` produces a long default report — use `NOPRINT` + `OUTPUT OUT=` for extraction pipelines

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=proc&docsetTarget=titlepage.htm

A bare `proc univariate` prints moments, location / variability, extreme
observations, missing-value counts, and plots for every numeric variable
listed in `VAR` — pages of output in a batch. For pipeline extraction
use `NOPRINT` and pull out named statistics via `OUTPUT OUT=`.

```sas
/* CORRECT - quiet extraction of specific statistics */
proc univariate data=claims noprint;
  var paid_amt;
  output out=paid_stats
    n=n mean=mean median=p50 q1=p25 q3=p75 p95=p95 p99=p99 max=max;
run;
```

```sas
/* WRONG - floods the output destination with every default panel */
proc univariate data=claims;
  var paid_amt;
run;
```

### Rule 8: `PROC PRINT VAR a b c;` orders columns; `NOOBS` drops the row-number column

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=proc&docsetTarget=titlepage.htm

Default PROC PRINT shows every variable in dataset order with a leading
`Obs` column. For inclusion in reports, restrict columns with `VAR`
(which also controls display order) and suppress the observation column
with `NOOBS`. Combine with `LABEL` to use variable labels for headers.

```sas
/* CORRECT - restricted to report columns, no Obs column, labels on */
proc print data=claims_summary noobs label;
  var member_id total_paid n_claims first_dt;
  label total_paid = 'Total Paid'
        n_claims   = 'Claim Count'
        first_dt   = 'First Claim Date';
run;
```

## Canonical Idioms

### Idiom: PROC FREQ minimum-count filter via `OUT=` + `WHERE=`

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=proc&docsetTarget=titlepage.htm

Purpose: generate a frequency table, keep only values with ≥ N
occurrences — common for privacy / small-cell-suppression filters and
for "what are the top dx codes" exploration.

```sas
proc freq data=claims noprint;
  tables dx_code / out=dx_freq(where=(count >= 10));
run;

proc sort data=dx_freq;
  by descending count;
run;
```

### Idiom: PROC MEANS CLASS-level summary → flat output dataset

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=proc&docsetTarget=titlepage.htm

Purpose: roll up `paid_amt` and `days_supply` per `member_id`, drop
the `_TYPE_` / `_FREQ_` bookkeeping columns, name output stats
explicitly. This is the single most common Base-SAS summarization
pattern in claims work.

```sas
proc means data=claims noprint;
  class member_id;
  var paid_amt days_supply;
  output out=claims_by_member(drop=_type_ _freq_)
    sum(paid_amt)    = total_paid
    sum(days_supply) = total_days
    n(paid_amt)      = n_claims;
run;
```

### Idiom: PROC SORT NODUPKEY dedup with audit tail

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=proc&docsetTarget=titlepage.htm

Purpose: dedup claims to one row per `member_id` + `service_dt`, but
preserve the duplicates in a separate dataset for QA review. `DUPOUT=`
captures exactly the rows that `NODUPKEY` discards.

```sas
proc sort data=claims
          out=claims_unique
          nodupkey
          dupout=claims_dupes;
  by member_id service_dt;
run;
```

### Idiom: PROC TRANSPOSE long → wide by `ID`

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=proc&docsetTarget=titlepage.htm

Purpose: pivot long-format visit records into one row per `member_id`
with columns `paid_1`, `paid_2`, ..., `paid_N`. The `ID` variable's
values become column-name suffixes; `PREFIX=` controls the stem.

```sas
proc sort data=claims_long;
  by member_id visit_seq;
run;

proc transpose data=claims_long
               out=claims_wide(drop=_name_)
               prefix=paid_;
  by member_id;
  id visit_seq;
  var paid_amt;
run;
```

## Function / Statement Quick Ref

| Name | Syntax | Purpose | Common mistake | Doc URL |
|------|--------|---------|----------------|---------|
| `PROC FREQ` | `proc freq; tables a*b / missing; run;` | One-way / cross-tabular counts | Default drops missing from cells and denominator | [PROC FREQ Procedure](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=proc&docsetTarget=titlepage.htm) |
| `PROC FREQ OUT=` | `tables x / out=ds noprint;` | Write frequencies to a dataset | Omitting `NOPRINT` on the PROC — still prints | [TABLES Statement OUT= Option](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=proc&docsetTarget=titlepage.htm) |
| `PROC MEANS` | `proc means; class g; var x; output out=ds sum=;` | Descriptive summary | Forgetting `NOPRINT` pollutes the listing | [PROC MEANS Procedure](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=proc&docsetTarget=titlepage.htm) |
| `PROC MEANS OUTPUT OUT=` | `output out=ds(drop=_type_ _freq_) sum()= mean()= ;` | Named output stats | Forgetting to drop `_TYPE_` / `_FREQ_` | [OUTPUT Statement (PROC MEANS)](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=proc&docsetTarget=titlepage.htm) |
| `PROC UNIVARIATE` | `proc univariate noprint; var x; output out=ds p25= p50= p75=;` | Quantiles + extended descriptives | Bare invocation produces pages of default report | [PROC UNIVARIATE Procedure](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=proc&docsetTarget=titlepage.htm) |
| `PROC SORT` | `proc sort data=a out=b; by v1 v2; run;` | Order rows | Omitting `OUT=` silently overwrites input | [PROC SORT Procedure](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=proc&docsetTarget=titlepage.htm) |
| `NODUPKEY` | `proc sort nodupkey; by k; run;` | Dedup by BY vars only | Mistaking for full-row dedup (`NODUPRECS`) | [NODUPKEY Option (PROC SORT)](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=proc&docsetTarget=titlepage.htm) |
| `NODUPRECS` | `proc sort noduprecs; by k; run;` | Full-row adjacent dedup | Only adjacent duplicates — sort first | [NODUPRECS Option (PROC SORT)](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=proc&docsetTarget=titlepage.htm) |
| `PROC TRANSPOSE` | `proc transpose out=b prefix=p_; by g; id seq; var x; run;` | Long ↔ wide reshape | Omitting `VAR` → every numeric transposes, chars silently dropped | [PROC TRANSPOSE Procedure](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=proc&docsetTarget=titlepage.htm) |
| `PROC REPORT` | `proc report nowd; column a b; define a / group; define b / analysis sum; run;` | Formatted report with grouping / summary | Using `DISPLAY` when `GROUP` was intended → no collapse | [PROC REPORT Procedure](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=proc&docsetTarget=titlepage.htm) |
| `PROC PRINT` | `proc print data=ds noobs label; var a b c; run;` | Listing report | Leaving default shows every column including bookkeeping vars | [PROC PRINT Procedure](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=proc&docsetTarget=titlepage.htm) |

## Silent Pitfalls

- **`PROC FREQ` drops missing by default** — `TABLES a*b` with missing
  in either dimension silently excludes those rows from both numerator
  and denominator. Use `/ MISSING` for "missing is a category" or
  `/ MISSPRINT` for "print but don't count". See Rule 1.
  Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=proc&docsetTarget=titlepage.htm

- **`PROC MEANS` prints even when you only asked for `OUTPUT OUT=`** —
  the output dataset is a side effect; the primary output is a printed
  table. `NOPRINT` on the PROC statement suppresses it. See Rule 2.
  Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=proc&docsetTarget=titlepage.htm

- **`PROC SORT` without `OUT=` overwrites the input** — the dataset
  you sorted is gone. See Rule 4. For non-destructive sort, always
  specify `OUT=`.
  Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=proc&docsetTarget=titlepage.htm

- **`NODUPKEY` vs `NODUPRECS` confusion** — `NODUPKEY` keeps the first
  row per BY group regardless of other columns; `NODUPRECS` only drops
  fully-duplicated adjacent rows. See Rule 3.
  Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=proc&docsetTarget=titlepage.htm

- **`PROC TRANSPOSE` with no `VAR` silently drops character columns** —
  transposes every `_NUMERIC_` variable, ignores chars, no warning.
  See Rule 5.
  Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=proc&docsetTarget=titlepage.htm

- **`PROC REPORT DEFINE ... / DISPLAY` when `GROUP` was intended** —
  the report shows every detail row instead of one-row-per-group. No
  error, just wrong shape. See Rule 6.
  Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=proc&docsetTarget=titlepage.htm

## Anti-patterns (STOP signs)

**STOP** when you see any of the following — the procedure runs to
completion but the output is almost certainly not what the author
meant:

- `proc freq; tables a*b; run;` with missing-bearing `a` or `b` → see
  Rule 1. Denominators silently exclude missings.
- `proc means; class g; var x; output out=ds sum=; run;` with no
  `NOPRINT` → see Rule 2. Unintended printed table.
- `proc sort data=claims; by ...; run;` with no `OUT=` → see Rule 4.
  Overwrites `claims`.
- `proc sort nodupkey; by member_id; run;` expecting full-row dedup →
  see Rule 3. All but first row per member_id lost.
- `proc transpose data=mixed out=wide; by g; id seq; run;` with no
  `VAR` → see Rule 5. Character columns silently dropped.
- `proc report; define key / display; ...` when summarization was
  intended → see Rule 6. Output has one row per detail, not per key.

## See Also

- [proc-sql.md](proc-sql.md) — SQL `SELECT DISTINCT` as an alternative
  to `PROC SORT NODUPKEY`; group-by summary as an alternative to
  `PROC MEANS`.
- [stat-procs.md](stat-procs.md) — statistical-modeling procedures
  (REG, GLM, LOGISTIC, GLIMMIX, MIXED); PROC UNIVARIATE normality /
  distribution tests.
- [ods-and-output.md](ods-and-output.md) — routing PROC MEANS /
  UNIVARIATE / REPORT output to Excel, RTF, PDF via ODS.
- [formats-informats.md](formats-informats.md) — `PROC FORMAT` value
  labels used by `PROC FREQ` / `PROC MEANS` / `PROC REPORT` for
  display.
- [Base SAS Procedures Guide](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=proc&docsetTarget=titlepage.htm)
