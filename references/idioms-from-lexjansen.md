---
title: Real-world SAS idioms (lexjansen / SUGI / SAS Global Forum)
scope: Distilled real-world idioms from lexjansen.com conference papers and SAS Global Forum / SUGI proceedings, cross-linked to the SAS-docs-grounded per-topic reference files. Hash (Dorfman), PROC SQL (Lafler), macro quoting (Whitlock, Lepp).
loaded_when: Unknown or novel task, "how do SAS programmers do X", "Dorfman hash", "Lafler PROC SQL", "Whitlock macro quoting", or when no single topic-reference file clearly matches the request.
last_reviewed: 2026-04-21
reviewer: xiaosongz
---

## Overview

This file is a curated set of idioms harvested from the lexjansen.com
archive and SAS Global Forum / SUGI proceedings — community-authored
conference papers that have circulated long enough to be recognized as
"the way SAS programmers actually do X." It complements the per-topic
reference files (`hash-tables.md`, `proc-sql.md`, `macros.md`) which
are grounded in the SAS 9.4 documentation; the idioms collected here
are grounded in practitioner lore instead. Every idiom cites the
specific conference paper URL plus author and venue, and quotes ≤90
verbatim words from any single paper.

The selection spans three clusters. The **hash cluster** draws on
Paul Dorfman's three canonical papers on the DATA-step hash object
(SUGI 30 2005, NESUG 2007, SESUG 2015) — the programming tool paper,
the Hash Crash tutorial, and the duplicate-key-entries paper. The
**PROC SQL cluster** draws on Kirk Paul Lafler's two WUSS / MWSUG
papers on CASE expressions and essential join techniques. The
**macro-quoting cluster** draws on Ian Whitlock's NESUG 2009 paper
("A Serious Look at Macro Quoting") and Tim Lepp's PhUSE 2019 paper
("SAS Macro Quoting - A Look Behind the Scenes"). Between them,
Whitlock and Lepp establish the compile-time / execution-time split
that governs which quoting function is correct in which context — a
distinction the SAS docs list without emphasis but that these papers
organize as a rule.

See also: the per-topic reference files cite a subset of these papers
alongside the SAS documentation, so overlap is expected and desired.
This file is the entry point when the task doesn't obviously map to a
single topic reference — "how do real SAS programmers stream a
lookup against a 50M-row claims extract," "when do I reach for
`%SUPERQ` vs `%NRSTR`," "what is the canonical `FULL JOIN` + COALESCE
pattern." For authoritative syntax, follow the cross-links back to
the topic reference file that cites the SAS docs directly.

## Critical Rules

### Rule 1: `%STR` / `%NRSTR` mask at compile time; `%BQUOTE` / `%NRBQUOTE` / `%SUPERQ` mask at execution time — pick by WHEN the offending symbol is seen, not by WHAT it is

Source: https://www.lexjansen.com/phuse/2019/sm/SM04.pdf

Lepp's rule, restated: "To mask static text input use %STR or %NRSTR.
To mask the content of &macro variables or %macro calls use %BQUOTE,
%NRBQUOTE or %SUPERQ." The macro compiler reads your source code
once; if the problematic character (semicolon, ampersand, unbalanced
quote) is in the literal source, a compile-time quoter applies. If
the problematic character is inside a `&var` value that doesn't exist
until run time, only an execution-time quoter can see it. Picking the
wrong tier is the single most common "why isn't my macro quoting
working" root cause Whitlock and Lepp both diagnose.

```sas
/* CORRECT - compile-time semicolon in literal text -> %STR;
   execution-time apostrophe inside an unknown claimant name -> %BQUOTE */
%let stmt_end = %str(;);                     /* literal semicolon in source */
%let patient_name = O'Brien;                 /* stored with a bare apostrophe */
%put quoted: %bquote(&patient_name) ;        /* execution-time mask */
```

```sas
/* WRONG - %STR on a macro variable value; the apostrophe is invisible
   at compile time, so %STR has nothing to quote. Macro processor
   hits the unbalanced apostrophe at run time and errors. */
%let patient_name = O'Brien;
%put quoted: %str(&patient_name) ;
```

### Rule 2: Load the SMALL side into the hash and stream the LARGE side with `set` — never the other way round

Source: https://www.lexjansen.com/nesug/nesug07/ff/ff03.pdf

Dorfman's Hash Crash paper is explicit: the hash object is a
memory-resident table whose footprint is the loaded rowcount times the
key + data portion width. Claims-data pipelines tempt the wrong
choice because the reference table (ICD-10, NDC, provider roster) is
always the small one, but Dorfman's examples show learners routinely
load the driver — a 10-50M-row claims extract — and OOM the session.
The rule: reference in the hash, driver through `set`.

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

### Rule 3: Searched CASE is the general form; simple CASE is for equality buckets only — prefer searched when in doubt

Source: https://www.lexjansen.com/wuss/2011/coders/Papers_Lafler_K_72492.pdf

Lafler: "the searched case expression offers the greatest flexibility
and is the primary form used by SQL'ers." The simple form
(`CASE col WHEN value THEN ...`) only handles equality against one
column; any range check, any combination of columns, any `UPCASE()`
wrap falls out of its grammar. Default to the searched form
(`CASE WHEN <full predicate> THEN ...`) unless you are genuinely
mapping one column to equality-based buckets.

```sas
/* CORRECT - searched CASE, combines two columns + a range predicate */
proc sql;
  create table claims_tagged as
  select member_id, service_dt, paid_amt,
    case
      when upcase(category) = 'INPATIENT'
        and paid_amt between 1000 and 10000  then 'inpt-mid'
      when upcase(category) = 'INPATIENT'
        and paid_amt >  10000                then 'inpt-high'
      when upcase(category) = 'OUTPATIENT'   then 'outpt'
      else                                        'other'
    end as claim_bucket
  from claims;
quit;
```

```sas
/* WRONG - simple CASE cannot express a range predicate on LENGTH
   nor combine two columns; silently compiles into nonsense. */
proc sql;
  select title, length,
    case length
      when < 120 then 'Short'
      when > 160 then 'Long'
      else            'Medium'
    end as movie_bucket
  from movies;
quit;
/* "case length when < 120" is not valid simple-CASE syntax — use searched. */
```

## Canonical Idioms

### Idiom: Dorfman streaming reference-table lookup (hash cluster)

Source: https://support.sas.com/resources/papers/proceedings/proceedings/sugi30/236-30.pdf

Paul Dorfman's SUGI 30 paper establishes the canonical many-to-one
hash lookup: load a small reference table into a hash on `_N_ = 1`,
then `set` the large driver dataset and call `find()` per row. The
PDV is type-matched with `if 0 then set ref;` — a no-op that populates
column types without reading a row. Dorfman frames this as the hash's
defining use case: "Attaching a descriptive column from a small
reference table onto every row of a large driver dataset without
pre-sorting either side." Claims-data version: ICD-10 description
table → claims; provider NPI roster → encounters.

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

### Idiom: Dorfman MULTIDATA + `find_next()` for one-to-many joins (hash cluster)

Source: https://www.lexjansen.com/sesug/2015/94_Final_PDF.pdf

Dorfman's 2015 SESUG paper covers the duplicate-key extension: with
`multidata: 'Y'` the hash accepts multiple entries per key, and
`find_next()` walks the duplicates for the current key. The classic
claims-data scenario is joining a claims driver to an eligibility
table that has one row per member per coverage span. Without
`multidata: 'Y'` only the first span survives; with it, a
`do while (rc = 0)` loop emits one output row per span, matching a
PROC SQL inner join without the sort.

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

### Idiom: Dorfman `check()` + `add()` deduplication (hash cluster)

Source: https://www.lexjansen.com/nesug/nesug07/ff/ff03.pdf

From the Hash Crash NESUG 2007 paper: the canonical "stream once,
keep the first row per composite key" idiom. `check()` asks "have I
seen this key?" without modifying the hash; `add()` inserts the new
key and the row is emitted. No pre-sort, no `NODUPKEY` pass — a
single DATA step over the driver. Useful in claims data for
"first-visit-per-patient" or "first-claim-per-provider-per-day"
deduplication where a PROC SORT would cost an extra pass over tens
of millions of rows.

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

### Idiom: Dorfman summary-less summarization with `find()` + `replace()` (hash cluster)

Source: https://www.lexjansen.com/nesug/nesug07/ff/ff03.pdf

Dorfman's Note 1 in the Hash Crash paper shows the hash as an
in-memory aggregator that sidesteps PROC SUMMARY's memory cost for
high-cardinality categorical variables: "if the only purpose is,
say, NWAY summarization, hash may do it much more economically." On
a miss, initialize the counter and `add()`; on a hit, increment and
`replace()`; on EOF, `output()` the hash to a persistent dataset.
Claims version: per-diagnosis counts, per-provider revenue rollups,
per-member claim-count histograms.

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

### Idiom: Lafler `LEFT JOIN` + `COALESCE` for reference-table attach (proc-sql cluster)

Source: https://www.lexjansen.com/mwsug/2015/RF/MWSUG-2015-RF-02.pdf

Lafler's MWSUG 2015 paper walks the full match-join matrix (inner,
left outer, right outer, full). The canonical claims-data form is
`LEFT JOIN` from the driver to a reference or eligibility table, with
`COALESCE` supplying a sentinel where the reference misses. Unlike
the DATA-step MERGE, Lafler notes that PROC SQL's "duplicate matching
column is not automatically overlaid" — meaning every shared column
must be qualified or coalesced in the SELECT or you get an ambiguous
reference at best, a silent overlay at worst.

```sas
proc sql;
  create table claims_plus as
  select c.member_id,
         c.service_dt,
         c.paid_amt,
         coalesce(e.plan_type, 'UNKNOWN') as plan_type
  from claims as c
  left join eligibility as e
    on  c.member_id  = e.member_id
   and c.service_dt between e.eff_dt and e.term_dt;
quit;
```

### Idiom: Lafler searched CASE for inline claim-cost bucketing (proc-sql cluster)

Source: https://www.lexjansen.com/wuss/2011/coders/Papers_Lafler_K_72492.pdf

Lafler's WUSS 2011 paper makes searched CASE the primary conditional
tool inside PROC SQL — "similar to an IF-THEN construct in the DATA
step, a case expression uses one or more WHEN-THEN clause(s) to
conditionally process some but not all the rows." The form is
cleaner than a secondary DATA step and keeps the bucketing logic
adjacent to the SELECT that uses it. Always include an `ELSE`; Lafler
stresses this as the "catch-all to prevent a missing value from being
assigned." In claims work the pattern attaches paid-amount buckets,
age bands, or LOS categories without a second pass.

```sas
proc sql;
  create table claims_tagged as
  select member_id,
         service_dt,
         paid_amt,
         case
           when paid_amt  =  0                         then 'zero-pay'
           when paid_amt  <  100                       then 'low'
           when paid_amt  <  1000                      then 'mid'
           when paid_amt  <  10000                     then 'high'
           else                                             'catastrophic'
         end as amt_bucket
  from claims;
quit;
```

### Idiom: Whitlock `%NRSTR` + `%UNQUOTE` to build a macro object at run time (macro-quoting cluster)

Source: https://www.lexjansen.com/nesug/nesug09/bb/BB02.pdf

Whitlock's NESUG 2009 paper demonstrates a subtle two-step: `%NRSTR`
hides an ampersand from the macro compiler so no resolution decision
is made, then `%UNQUOTE` at execution time glues the ampersand to a
run-time-generated variable name, producing a reference the macro
facility evaluates. Useful when a variable name itself is built from
a macro call — rare in straightforward pipelines, critical in
code-generation macros that emit `%let &var = ...` targets where
`&var` is not known until run time.

```sas
/* Whitlock's NESUG 2009 paper uses bare `%macro makename;` (no parens).
   Parens added here to comply with sasjs/lint hasMacroParentheses;
   pattern is otherwise identical. */
%macro makename();
  claim_count_2024
%mend makename;

%macro set_and_read();
  %let %makename = 77;
  %put %unquote(%nrstr(&)%makename);   /* prints 77, not &claim_count_2024 */
%mend set_and_read;

%set_and_read
```

### Idiom: Lepp `%SUPERQ` for one-shot "freeze the value exactly" reads (macro-quoting cluster)

Source: https://www.lexjansen.com/phuse/2019/sm/SM04.pdf

Lepp identifies `%SUPERQ` as "the actual sister function to `%NRSTR`
at execution time" — it takes a macro variable *name* (no leading
`&`) and returns the value with every `&` and `%` trigger masked,
without attempting resolution. The right tool when a claimant name,
provider name, or operating-system path contains characters that
would otherwise fire warnings. Unlike `%BQUOTE`, `%SUPERQ` does not
resolve nested macro references inside the value first, which is the
desired behavior when the value is user-supplied data rather than
generated code.

```sas
%let ptname = O'Brien & Sons, %% discount;       /* nasty literal */

/* CORRECT - %SUPERQ freezes the exact stored value */
%put frozen: %superq(ptname) ;

/* CONTRAST - %BQUOTE would first try to resolve macro triggers and
   emit warnings about &Sons / %discount before masking. */
```

## Function / Statement Quick Ref

| Name | Idiom / Pattern | Paper | URL |
|------|-----------------|-------|-----|
| Reference lookup via hash | small-ref in hash, large-driver via `set` | Dorfman, SUGI 30 (2005) | [236-30.pdf](https://support.sas.com/resources/papers/proceedings/proceedings/sugi30/236-30.pdf) |
| Hash Crash tutorial | `check()`+`add()` dedup, `find()`+`replace()` counter | Dorfman, NESUG 2007 | [ff03.pdf](https://www.lexjansen.com/nesug/nesug07/ff/ff03.pdf) |
| Duplicate-key hash | `multidata: 'Y'` + `find_next()` one-to-many | Dorfman, SESUG 2015 | [94_Final_PDF.pdf](https://www.lexjansen.com/sesug/2015/94_Final_PDF.pdf) |
| PROC SQL CASE | searched CASE for row-level conditional columns | Lafler, WUSS 2011 | [Papers_Lafler_K_72492.pdf](https://www.lexjansen.com/wuss/2011/coders/Papers_Lafler_K_72492.pdf) |
| PROC SQL joins | LEFT / RIGHT / FULL + COALESCE | Lafler, MWSUG 2015 | [MWSUG-2015-RF-02.pdf](https://www.lexjansen.com/mwsug/2015/RF/MWSUG-2015-RF-02.pdf) |
| Macro quoting tiers | compile-time vs execution-time split; `%STR` / `%NRSTR` vs `%BQUOTE` / `%NRBQUOTE` / `%SUPERQ` | Whitlock, NESUG 2009 | [BB02.pdf](https://www.lexjansen.com/nesug/nesug09/bb/BB02.pdf) |
| Macro quoting mechanics | ID-byte masking scheme and timing; `%UNQUOTE` as run-time reveal | Lepp, PhUSE 2019 | [SM04.pdf](https://www.lexjansen.com/phuse/2019/sm/SM04.pdf) |

## Topic Cluster Summary

**Hash cluster (Dorfman, 3 papers).** The 2005 SUGI 30 paper is the
tutorial of record — it introduces the `declare hash` / `definekey` /
`definedata` / `definedone` sequence, the iterator (`hiter`), and
the `if _N_ = 1 then do; ... end;` scoping pattern. The 2007 NESUG
"Hash Crash" paper extends this with aggregation idioms (the
summary-less summarization note) and the memory-footprint warning
that anchors Rule 2 above. The 2015 SESUG paper fills in the
`multidata: 'Y'` / `find_next()` mechanics that make one-to-many
joins possible without PROC SQL. The per-topic file `hash-tables.md`
cites all three and encodes their rules as DATA-step-documentation-grounded
syntax; this file documents them as *named idioms* with the
practitioner history attached.

**PROC SQL cluster (Lafler, 2 papers).** The WUSS 2011 paper is
narrowly about CASE expressions — simple vs searched, the `ELSE`
catch-all, and the claim that searched CASE is the primary form
practitioners reach for. The MWSUG 2015 paper is a guided tour of
the match-join matrix with Venn-diagram illustrations, and is the
source for the "duplicate matching column is not automatically
overlaid" rule that anchors `proc-sql.md` Rule 1. Together they cover
the two most common claims-analytics uses of PROC SQL: row-level
conditional columns and reference-table joins. Note: a third Lafler
paper ("Best Tips and Techniques Using PROC SQL", SGF 2011 paper 101)
was in our scraper seeds but the cached file turned out to contain a
different paper (Gamishev on email management) — it is not cited
here. The SGF 2011 Lafler paper is not available via our current
cache; re-scraping is a separate task.

**Macro-quoting cluster (Whitlock + Lepp, 2 papers).** Whitlock's
NESUG 2009 paper is the long-form explanation of why macro quoting
even exists — "the fact that [the] same word or combination of
symbols can have meanings in both SAS and macro that is the root
cause for requiring quoting" — and walks through `%STR`, `%NRSTR`,
`%QUOTE`, `%BQUOTE`, `%NRQUOTE`, `%NRBQUOTE`, `%SUPERQ`, and
`%UNQUOTE` with worked examples. Lepp's PhUSE 2019 paper is the
complementary short-form: it diagrams the Input Stack / Word Scanner
/ Macro Processor interaction and shows how the compile-time /
execution-time split falls out of the processing order. The
Whitlock paper is the "why"; the Lepp paper is the "when." Rule 1
above is Lepp's four-bullet conclusion, verbatim in spirit.

## Silent Pitfalls

- **Citing an idiom to the wrong paper** — this file covers seven
  distinct papers; the Dorfman corpus in particular has overlapping
  coverage (all three Dorfman papers touch `find()` / `add()`). Use
  the Source URL as the single source of truth, not the topic
  cluster heading.
  Source: https://support.sas.com/resources/papers/proceedings/proceedings/sugi30/236-30.pdf

- **Conflating `%BQUOTE` and `%SUPERQ`** — both are
  execution-time quoters, but `%BQUOTE(&var)` resolves nested
  references inside the value first, while `%SUPERQ(var)` (note: no
  ampersand) does not. Lepp's PhUSE paper is explicit that `%SUPERQ`
  is "the actual sister function to `%NRSTR` at execution time." For
  truly user-supplied data, `%SUPERQ` is safer.
  Source: https://www.lexjansen.com/phuse/2019/sm/SM04.pdf

- **Loading the driver into the hash** — a claims-scale hash OOMs
  the session when the driver is the 50M-row side. Dorfman's 2007
  paper makes this the opening caution; Rule 2 above restates it.
  Hash is for the *small* side of the join.
  Source: https://www.lexjansen.com/nesug/nesug07/ff/ff03.pdf

- **Silent collapse on duplicate keys** — without `multidata: 'Y'`
  a duplicate key `add()` returns non-zero and the incoming row is
  dropped. Dorfman's 2015 SESUG paper documents this as the default;
  the remedy is the `multidata: 'Y'` + `find_next()` idiom above.
  Source: https://www.lexjansen.com/sesug/2015/94_Final_PDF.pdf

- **Simple CASE with range predicates** — Lafler's WUSS paper shows
  `CASE length WHEN < 120 THEN ...` as an anti-example: the simple
  form only handles equality. Use searched CASE when the predicate
  is anything richer than `col = value`.
  Source: https://www.lexjansen.com/wuss/2011/coders/Papers_Lafler_K_72492.pdf

## Anti-patterns (STOP signs)

**STOP** when you see any of the following — the code may compile and
produce output, but the output is almost certainly not what the
author meant:

- `%str(&var)` where `&var` holds a quote character or ampersand —
  `%STR` is a compile-time directive; the resolution of `&var`
  happens later, so there is nothing for `%STR` to mask. Use
  `%BQUOTE(&var)` or `%SUPERQ(var)` (Rule 1).
- `declare hash big(dataset: 'claims');` on a 50M-row claims table —
  the hash is the wrong shape for this job; switch to PROC SQL or a
  DATA-step MERGE (Rule 2).
- `declare hash e(dataset: 'eligibility');` on a table with multiple
  rows per member — drops every coverage span but the first (see
  MULTIDATA idiom).
- `case col when < 120 then ...` — simple CASE grammar does not
  accept a comparison operator; rewrite as searched CASE (Rule 3).
- `left join b on a.k = b.k` followed by `select a.*, b.*` where
  both tables have a shared non-key column — silent overlay of one
  column onto the other. See `proc-sql.md` Rule 1 for the qualifier /
  COALESCE remedy.
- Citing `lafler-2011-sgf-procsql-tips.md` in this repo — the
  cached file at that path contains Gamishev's SGF 2011 paper 101
  on email management, not Lafler. Use the two cited Lafler papers
  (WUSS 2011 and MWSUG 2015) instead.

## See Also

- [hash-tables.md](hash-tables.md) — SAS-docs-grounded hash rules;
  cites the three Dorfman papers inline as Rule / Idiom sources.
- [proc-sql.md](proc-sql.md) — SAS-docs-grounded PROC SQL rules;
  cites the two Lafler papers inline.
- [macros.md](macros.md) — SAS-docs-grounded macro language rules;
  quoting tier summary complements Whitlock / Lepp here.
- [data-step.md](data-step.md) — DATA-step control flow and MERGE
  semantics; see the "SQL join vs MERGE" rule for the counterpart to
  the hash streaming idiom.
- [Dorfman (2005) — Data Step Hash Objects as Programming Tools](https://support.sas.com/resources/papers/proceedings/proceedings/sugi30/236-30.pdf)
- [Dorfman (2007) — Hash Crash and Beyond](https://www.lexjansen.com/nesug/nesug07/ff/ff03.pdf)
- [Dorfman (2015) — Using the SAS Hash Object with Duplicate Key Entries](https://www.lexjansen.com/sesug/2015/94_Final_PDF.pdf)
- [Lafler (2011) — Conditional Processing Using the Case Expression in PROC SQL](https://www.lexjansen.com/wuss/2011/coders/Papers_Lafler_K_72492.pdf)
- [Lafler (2015) — Essential PROC SQL Join Techniques](https://www.lexjansen.com/mwsug/2015/RF/MWSUG-2015-RF-02.pdf)
- [Whitlock (2009) — A Serious Look at Macro Quoting](https://www.lexjansen.com/nesug/nesug09/bb/BB02.pdf)
- [Lepp (2019) — SAS Macro Quoting: A Look Behind the Scenes](https://www.lexjansen.com/phuse/2019/sm/SM04.pdf)
