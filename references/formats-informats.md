---
title: Formats and informats reference
scope: PROC FORMAT (`VALUE` / `INVALUE` / `PICTURE`), user-defined formats via `CNTLIN=`, date / time / datetime formats and informats (`mmddyy10.`, `yymmdd10.`, `datetime20.`, `anydtdte.`), `input()` / `put()` conversion functions, `DATESTYLE=` system option.
loaded_when: '"PROC FORMAT", "VALUE", "INVALUE", "PICTURE", "CNTLIN", "put(", "input(", "mmddyy", "yymmdd", "datetime", "anydtdte", "informat", "format statement", or any user-defined format / informat or date parsing task.'
last_reviewed: 2026-04-21
reviewer: xiaosongz
---

## Overview

Formats and informats are SAS's bidirectional bridge between stored
values and their human-readable representations. A **format**
converts a stored value into a character string for display
(`put(x, dollar12.2)` → `'$1,234.56'`); an **informat** converts an
input character string into a stored value (`input('01/02/2020',
mmddyy10.)` → the SAS date number `21916`). Every format name ends
in a period when referenced (`format dob mmddyy10.;`) and lacks one
when defined in `PROC FORMAT VALUE` (`value $cpt_cat '99201'='E&M';`)
— the trailing dot is what distinguishes format-reference from
variable-name in every context that accepts both.

PROC FORMAT builds user-defined formats via three statements —
`VALUE` (character-label for value or range), `INVALUE` (value or
range for input string), and `PICTURE` (digit-selector template for
numbers) — or from a dataset via `CNTLIN=`. User formats attach to
variables via `FORMAT var fmt.;` in a DATA step, SET, MERGE, or PROC;
they render on display without altering the stored value, so
`sum(paid_amt)` works the same whether or not a `DOLLAR` format is
attached. The direction confusion — `put()` vs `input()`, FORMAT vs
INFORMAT — is the most common bug; this file encodes the rules from
the SAS Formats and Informats Reference (leforinforref) and the
PROC FORMAT chapter of the Base SAS Procedures Guide (proc).

See also `data-step.md` for the `FORMAT` / `LENGTH` / `ATTRIB`
statements that attach formats to variables, and
`functions-reference.md` for the full surface of `INPUT()` and
`PUT()` functions plus date arithmetic helpers.

## Critical Rules

### Rule 1: `put()` goes variable → string; `input()` goes string → variable — inverting them silently returns wrong values

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=leforinforref&docsetTarget=titlepage.htm

`put(date, mmddyy10.)` reads a numeric SAS date and returns a
character string `'01/02/2020'`. `input('01/02/2020', mmddyy10.)`
reads a character string and returns the numeric SAS date `21916`.
The two functions share an argument shape but move data in opposite
directions. The classic bug: writing `put(date_str, mmddyy10.)`
where `date_str` is already a character column — SAS treats the
character string as a raw number, either producing garbage or a
type-mismatch NOTE but never what the author meant.

```sas
/* CORRECT - put formats a number, input parses a string */
data dates;
  sas_date = '15MAR2024'd;                        /* numeric */
  date_str = put(sas_date, mmddyy10.);            /* -> '03/15/2024' */
  back = input(date_str, mmddyy10.);              /* -> 23451 */
run;
```

```sas
/* WRONG - put() on a string argument; silently returns garbage */
data bad;
  date_str = '03/15/2024';
  sas_date = put(date_str, mmddyy10.);  /* type mismatch; not a parse */
run;
```

### Rule 2: Every format reference ends in a period (`.`); every format definition in `VALUE` does NOT

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=proc&docsetTarget=titlepage.htm

When you **reference** a format (in a `FORMAT` statement, a `PUT`
function, or a `PUT` statement), the name ends in a period:
`format dob mmddyy10.;`. When you **define** a user format in
`PROC FORMAT VALUE` / `PICTURE` / `INVALUE`, the name does not:
`value $cpt_cat ...`. The trailing dot disambiguates format names
from variable names in contexts that accept both. Omit the dot on
reference and SAS looks for a variable named `mmddyy10`, usually
triggering an uninitialized-variable NOTE and an unformatted
display.

```sas
/* CORRECT - trailing dot on reference, none on VALUE definition */
proc format;
  value agegrp low-17='Minor' 18-64='Adult' 65-high='Senior';
run;

data demo_fmt;
  set demo;
  format age agegrp.;
run;
```

```sas
/* WRONG - no trailing dot on reference */
proc format;
  value agegrp low-17='Minor' 18-64='Adult' 65-high='Senior';
run;

data demo_fmt;
  set demo;
  format age agegrp;  /* NOTE: Variable AGEGRP is uninitialized. */
run;
```

### Rule 3: `anydtdte.` resolves ambiguous dates using the `DATESTYLE=` system option — set it explicitly

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=leforinforref&docsetTarget=titlepage.htm

`anydtdte.` is a permissive date informat: it accepts most
string forms (`01JAN2020`, `2020-01-15`, `03/15/2024`). When the
input is ambiguous — `01/02/2020` could be Jan 2 or Feb 1 — SAS
consults the `DATESTYLE=` system option. The default is locale-
dependent (US installs default to MDY; many European locales to
DMY), so the same script on different hosts silently produces
different dates. Always set `options datestyle=mdy;` (or DMY)
before reading ambiguous strings.

```sas
/* CORRECT - explicit DATESTYLE; same result on every host */
options datestyle=mdy;
data parsed;
  raw = '01/02/2020';
  srvc_date = input(raw, anydtdte10.);  /* -> 02JAN2020 */
  format srvc_date mmddyy10.;
run;
```

```sas
/* WRONG - DATESTYLE inherits locale default; US = 02JAN, EU = 01FEB */
data parsed;
  raw = '01/02/2020';
  srvc_date = input(raw, anydtdte10.);
run;
```

### Rule 4: `VALUE` ranges need an `other=` clause — unmapped values otherwise display as their raw form, not the mapped label

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=proc&docsetTarget=titlepage.htm

`PROC FORMAT VALUE` only rewrites values that fall inside one of
the listed ranges. Values outside every range pass through
unchanged — numeric 99 becomes the string `'99'`, not a mapped
label. For classification formats the almost-always-correct
behavior is to add `other='Unknown'` (or a sentinel like `'ZZ'`)
so unmapped values surface visibly. Without it, a broken mapping
shows up as a mix of labels and raw codes in the output.

```sas
/* CORRECT - explicit OTHER catches anything not listed */
proc format;
  value $cpt_cat
    '99201'-'99499' = 'E&M'
    '20000'-'29999' = 'Surgery'
    '70000'-'79999' = 'Radiology'
    other           = 'Other';
run;
```

```sas
/* WRONG - no OTHER; unmapped CPTs display as the raw code */
proc format;
  value $cpt_cat
    '99201'-'99499' = 'E&M'
    '20000'-'29999' = 'Surgery';
run;
/* a CPT of '73030' formats as '73030' — not grouped as 'Other' */
```

### Rule 5: `CNTLIN=` requires columns `FMTNAME`, `START`, `LABEL` — plus `TYPE='C'` for character formats and `END` for ranges

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=proc&docsetTarget=titlepage.htm

`proc format cntlin=fmt_ds;` builds a format from a dataset
without writing any `VALUE` statements. The control dataset must
contain `FMTNAME` (the format name), `START` (the low boundary or
the value), and `LABEL` (the formatted string). For character
formats add `TYPE='C'` (or prefix FMTNAME with `$`); for ranges
add an `END` column. `START` and `END` must have the same length,
or SAS errors. A common bug is building the dataset with different
`$9.` and `$8.` lengths and getting a non-obvious `ERROR:`.

```sas
/* CORRECT - minimal character-format control dataset */
data fmt_plan;
  length fmtname $8 start end $4 label $20 type $1;
  fmtname='$plan'; type='C';
  start='HMO';  end='HMO';  label='HMO plan';     output;
  start='PPO';  end='PPO';  label='PPO plan';     output;
  start='POS';  end='POS';  label='Point of Svc'; output;
run;

proc format cntlin=fmt_plan; run;
```

```sas
/* WRONG - START is $4, END is $5; "lengths must be the same" error */
data fmt_bad;
  length fmtname $8 start $4 end $5 label $20;
  fmtname='$plan'; start='HMO'; end='HMO'; label='HMO';
run;
proc format cntlin=fmt_bad; run;
```

### Rule 6: FORMAT (display) and INFORMAT (parse) are distinct attributes — using `FORMAT` where `INFORMAT` is needed silently reads garbage

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=leforinforref&docsetTarget=titlepage.htm

The `FORMAT` statement attaches a display format to a variable;
it has no effect on how SAS reads raw text. The `INFORMAT`
statement tells SAS how to parse an input column. In a DATA step
with `INPUT`, using `format date mmddyy10.;` without `informat`
parses the raw column with the default `w.d` numeric informat —
producing missings or garbage — then displays the garbage with
`mmddyy10.`. Always pair them when reading date strings:
`informat date mmddyy10.; format date mmddyy10.;`.

```sas
/* CORRECT - INFORMAT parses, FORMAT displays */
data visits;
  infile 'visits.csv' dsd;
  informat srvc_date mmddyy10.;
  format srvc_date mmddyy10.;
  input patient_id srvc_date paid_amt;
run;
```

```sas
/* WRONG - only FORMAT; SAS parses srvc_date as numeric, gets missing */
data visits;
  infile 'visits.csv' dsd;
  format srvc_date mmddyy10.;
  input patient_id srvc_date paid_amt;
run;
```

### Rule 7: Format width controls display truncation but NOT stored precision

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=leforinforref&docsetTarget=titlepage.htm

`format x 5.;` limits the printed width to 5 characters — a
6-digit integer prints as `*****` (the overflow indicator). The
stored 8-byte numeric is unaffected; subsequent PROCs still see
the full value. This is the mirror bug of "I set the format so my
value is wrong" — it isn't wrong, just hidden. Use `best12.` or
a wider `w.d` when unsure; use narrower widths deliberately for
columnar reports.

```sas
/* CORRECT - wide enough for realistic paid amounts */
data costs_display;
  set costs;
  format paid_amt dollar12.2;
run;
```

```sas
/* WRONG - format 6.2 truncates paid_amt = 1234.56 to **** */
data costs_display;
  set costs;
  format paid_amt 6.2;
run;
/* the stored value is still 1234.56 but displays as asterisks */
```

### Rule 8: `PICTURE` digit selectors — `9` is a required digit, `0` is leading-zero-filled, other characters are literals

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=proc&docsetTarget=titlepage.htm

`PICTURE` format templates use `9` for a display digit that takes
the corresponding numeric position, `0` for a digit that fills
with a leading zero if no numeric position exists, and any other
character (`$`, `,`, `%`, space) as a literal passed through.
`picture mybucks low-high = '000,000,009.99' (prefix='$');`
renders 12.3 as `$000,000,012.30`. Order matters: the rightmost
digit selector maps to the number's ones place. Forgetting this
produces misaligned commas or unexpected zero-padding.

```sas
/* CORRECT - picture format for claim IDs as zero-padded 9-digit */
proc format;
  picture claimid low-high = '000000009';
run;
data ids;
  id = 42;
  formatted = put(id, claimid9.);   /* -> '000000042' */
run;
```

```sas
/* WRONG - all 9s; no leading zero pad on small numbers */
proc format;
  picture claimid low-high = '999999999';
run;
data ids;
  id = 42;
  formatted = put(id, claimid9.);   /* -> '       42' */
run;
```

## Canonical Idioms

### Idiom: Build a claims-aware character format for CPT / ICD code categorization

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=proc&docsetTarget=titlepage.htm

Purpose: collapse thousands of CPT / ICD codes into a handful of
analytic categories via a `VALUE` format, then apply with `put()`
in a DATA step. No joins, no merges — reference-table logic lives
in the format catalog.

```sas
proc format;
  value $cpt_cat
    '99201'-'99499' = 'E&M'
    '20000'-'29999' = 'Surgery'
    '70000'-'79999' = 'Radiology'
    '80000'-'89999' = 'Pathology / Lab'
    '90000'-'99199' = 'Medicine'
    other           = 'Other';
run;

data claims_tagged;
  set claims;
  cpt_category = put(cpt_code, $cpt_cat.);
run;
```

### Idiom: Parse a messy date column with `anydtdte.` plus explicit `DATESTYLE=`

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=leforinforref&docsetTarget=titlepage.htm

Purpose: claims extracts often arrive with heterogeneous date
strings across vendors (`01/15/2024`, `2024-01-15`, `15JAN2024`).
`anydtdte.` handles all three; the `options datestyle=mdy;` pins
the interpretation of ambiguous MDY-vs-DMY forms so the script is
host-agnostic.

```sas
options datestyle=mdy;

data claims_clean;
  set claims_raw;
  srvc_date = input(date_str, anydtdte32.);
  format srvc_date mmddyy10.;
  if missing(srvc_date) then put 'WARN: unparsed date ' date_str=;
run;
```

### Idiom: Build a user format from a dataset via `CNTLIN=`

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=proc&docsetTarget=titlepage.htm

Purpose: when the mapping is already maintained as a CSV / SAS
dataset (ICD-10 chapter table, provider taxonomy crosswalk),
generate the format programmatically instead of hand-writing
thousands of `VALUE` lines. The control dataset's three columns —
`FMTNAME`, `START`, `LABEL` — are all that's required for a simple
equality mapping.

```sas
data fmt_icd_chapter;
  length fmtname $8 start $7 label $40;
  fmtname = '$icdch';
  set icd10_chapter_crosswalk(rename=(code=start chapter_name=label));
run;

proc format cntlin=fmt_icd_chapter; run;

data claims_chaptered;
  set claims;
  chapter = put(dx_code, $icdch.);
run;
```

### Idiom: `input()` inside a DATA step to coerce a numeric-looking character column

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=leforinforref&docsetTarget=titlepage.htm

Purpose: pipeline handoff bug — a numeric column arrives as
character (`'1234.56'`) because it was read from CSV with default
informats. Convert it inline with `input(str, best.)` rather than
a round-trip through PROC SQL or a rename.

```sas
data costs_num;
  set costs_char;
  paid_num = input(paid_str, best12.);
  format paid_num dollar12.2;
  drop paid_str;
run;
```

## Function / Statement Quick Ref

| Name | Syntax | Purpose | Common mistake | Doc URL |
|------|--------|---------|----------------|---------|
| `PROC FORMAT` | `proc format; stmts; run;` | Create user formats / informats | No `LIBRARY=` → format is WORK-session scoped | [`PROC FORMAT`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=proc&docsetTarget=titlepage.htm) |
| `VALUE` | `value name range1=label1 range2=label2 other=...;` | Define a format | No `OTHER=` → unmapped values pass through raw (Rule 4) | [`VALUE Statement`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=proc&docsetTarget=titlepage.htm) |
| `INVALUE` | `invalue name range1=val1 ...;` | Define an informat | Using where `VALUE` was meant; direction inversion | [`INVALUE Statement`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=proc&docsetTarget=titlepage.htm) |
| `PICTURE` | `picture name low-high='9,999.99' (prefix='$');` | Digit-selector numeric template | `9` vs `0` confusion on leading pads (Rule 8) | [`PICTURE Statement`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=proc&docsetTarget=titlepage.htm) |
| `CNTLIN=` | `proc format cntlin=ds; run;` | Build format from dataset | START / END length mismatch errors (Rule 5) | [`CNTLIN= option`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=proc&docsetTarget=titlepage.htm) |
| `CNTLOUT=` | `proc format cntlout=ds; run;` | Dump catalog to dataset for audit | Not specifying `LIBRARY=`; defaults to WORK | [`CNTLOUT= option`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=proc&docsetTarget=titlepage.htm) |
| `FORMAT` stmt | `format var fmt.;` | Attach display format to variable | No trailing dot on reference (Rule 2) | [`FORMAT Statement`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=leforinforref&docsetTarget=titlepage.htm) |
| `INFORMAT` stmt | `informat var fmt.;` | Attach parse informat to variable | Using `FORMAT` instead; silent parse failure (Rule 6) | [`INFORMAT Statement`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=leforinforref&docsetTarget=titlepage.htm) |
| `put()` | `str = put(num, fmt.);` | Numeric / char → formatted string | Applying to already-character input (Rule 1) | [`PUT Function`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=leforinforref&docsetTarget=titlepage.htm) |
| `input()` | `num = input(str, infmt.);` | String → numeric / date / time | Using `put()` by mistake (Rule 1) | [`INPUT Function`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=leforinforref&docsetTarget=titlepage.htm) |
| `putn()` / `putc()` | `str = putn(num, 'mmddyy10.');` | Format name supplied as run-time string | Forgetting the name must end in `.` inside the string | [`PUTN / PUTC`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=leforinforref&docsetTarget=titlepage.htm) |
| `inputn()` / `inputc()` | `num = inputn(str, 'mmddyy10.');` | Informat name supplied as run-time string | Forgetting the trailing `.` | [`INPUTN / INPUTC`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=leforinforref&docsetTarget=titlepage.htm) |
| `mmddyy10.` | `format dob mmddyy10.;` | US-style `MM/DD/YYYY` date display | Confusing with informat direction | [`MMDDYYw. Format`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=leforinforref&docsetTarget=titlepage.htm) |
| `yymmdd10.` | `format dob yymmdd10.;` | ISO-style `YYYY-MM-DD` display | Width 8 drops century digits | [`YYMMDDw. Format`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=leforinforref&docsetTarget=titlepage.htm) |
| `datetime20.` | `format ts datetime20.;` | Date + time display | Confusing with `date` informat (strips time) | [`DATETIMEw. Format`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=leforinforref&docsetTarget=titlepage.htm) |
| `anydtdte.` | `dt = input(s, anydtdte32.);` | Permissive date informat | Missing `DATESTYLE=` (Rule 3) | [`ANYDTDTEw. Informat`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=leforinforref&docsetTarget=titlepage.htm) |
| `best.` | `x = input(str, best12.);` | Auto-pick numeric width | Misreading commas / parens as non-numeric | [`BESTw. Format / Informat`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=leforinforref&docsetTarget=titlepage.htm) |
| `dollar.` | `format paid dollar12.2;` | Currency display with `$` and commas | Too-narrow width → asterisks (Rule 7) | [`DOLLARw.d Format`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=leforinforref&docsetTarget=titlepage.htm) |
| `options datestyle=` | `options datestyle=mdy;` | Pin ambiguous-date interpretation | Leaving default; host locale varies (Rule 3) | [`DATESTYLE= Option`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=leforinforref&docsetTarget=titlepage.htm) |

## Silent Pitfalls

- **`put()` / `input()` inversion** — `put()` formats a stored
  value for display; `input()` parses an input string. Swapping
  them silently returns wrong values (or triggers a type-mismatch
  NOTE that gets buried in log noise). See Rule 1.
  Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=leforinforref&docsetTarget=titlepage.htm

- **Missing trailing dot on format reference** — `format age agegrp;`
  with no dot makes SAS look for a variable named `agegrp`. See
  Rule 2.
  Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=proc&docsetTarget=titlepage.htm

- **`anydtdte.` with locale-defaulted `DATESTYLE`** — same input
  string parses to a different date on US vs EU hosts. Always set
  `options datestyle=mdy;` explicitly. See Rule 3.
  Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=leforinforref&docsetTarget=titlepage.htm

- **`VALUE` format with no `OTHER=`** — unmapped values pass through
  raw, mixing labels and codes in the output. See Rule 4.
  Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=proc&docsetTarget=titlepage.htm

- **`FORMAT` used where `INFORMAT` is needed** — SAS parses with
  default `w.d` and produces missings or garbage, then displays the
  garbage with the attached FORMAT. See Rule 6.
  Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=leforinforref&docsetTarget=titlepage.htm

- **Format width narrower than the value** — `format x 5.;`
  truncates display to `*****`; the stored value is still full
  precision. See Rule 7.
  Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=leforinforref&docsetTarget=titlepage.htm

- **CNTLIN START / END length mismatch** — an easy-to-miss data-prep
  error that yields an opaque PROC FORMAT error. See Rule 5.
  Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=proc&docsetTarget=titlepage.htm

## Anti-patterns (STOP signs)

**STOP** when you see any of the following — the code runs but the
values are almost certainly not what the author meant:

- `put(char_var, mmddyy10.)` or `input(num_var, best.)` — direction
  inversion. See Rule 1.
- `format dob mmddyy10` (no trailing dot) → SAS searches for
  variable `mmddyy10`. See Rule 2.
- `input(s, anydtdte10.)` with no `options datestyle=` → host-locale
  silent divergence. See Rule 3.
- `value $grp 'A'='Alpha' 'B'='Beta';` with no `other=` and unmapped
  inputs expected to surface as `'Other'` → see Rule 4.
- `proc format cntlin=ds;` where `ds` lacks `FMTNAME` / `START` /
  `LABEL`, or has length-mismatched `START`/`END` → see Rule 5.
- DATA step with `format date mmddyy10.;` but no `informat`, reading
  a text column → see Rule 6.
- `format paid_amt 6.2;` on dollar-scale data → display truncates
  to asterisks. See Rule 7.

## See Also

- [data-step.md](data-step.md) — `FORMAT` / `INFORMAT` / `LENGTH`
  / `ATTRIB` statements in a DATA step; where and when attached
  attributes propagate to the output dataset.
- [functions-reference.md](functions-reference.md) — full surface
  of `INPUT()` / `PUT()` / `INPUTN` / `PUTN` plus date-arithmetic
  functions (`INTCK`, `INTNX`, `MDY`, `DATEPART`, `TIMEPART`).
- [base-procs.md](base-procs.md) — `PROC FREQ` / `PROC MEANS` /
  `PROC REPORT` all honor attached formats for display grouping.
- [proc-sql.md](proc-sql.md) — format-based `CASE` alternatives and
  `put()` usage in a SELECT list.
- [SAS Formats and Informats: Reference (9.4)](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=leforinforref&docsetTarget=titlepage.htm)
- [Base SAS Procedures Guide — FORMAT Procedure (9.4)](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=proc&docsetTarget=titlepage.htm)
