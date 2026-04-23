---
title: PROC FORMAT — VALUE / INVALUE / PICTURE / CNTLIN
loaded_when: '"PROC FORMAT", "VALUE", "INVALUE", "PICTURE", "CNTLIN", "CNTLOUT", "user-defined format", "format catalog", or any task that defines or audits a user format / informat.'
---

## Critical Rules

### Rule 4: `VALUE` ranges need an `other=` clause — unmapped values otherwise display as their raw form, not the mapped label

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

### Rule 8: `PICTURE` digit selectors — `9` is a required digit, `0` is leading-zero-filled, other characters are literals

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

### Build a claims-aware character format for CPT / ICD code categorization

Collapse thousands of CPT / ICD codes into a handful of analytic
categories via a `VALUE` format, then apply with `put()` in a DATA
step. No joins, no merges — reference-table logic lives in the
format catalog.

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

### Build a user format from a dataset via `CNTLIN=`

When the mapping is already maintained as a CSV / SAS dataset
(ICD-10 chapter table, provider taxonomy crosswalk), generate the
format programmatically instead of hand-writing thousands of
`VALUE` lines. The control dataset's three columns — `FMTNAME`,
`START`, `LABEL` — are all that's required for a simple equality
mapping.

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

## Quick Ref

| Name | Syntax | Purpose | Common mistake |
|------|--------|---------|----------------|
| `PROC FORMAT` | `proc format; stmts; run;` | Create user formats / informats | No `LIBRARY=` → format is WORK-session scoped |
| `VALUE` | `value name range1=label1 range2=label2 other=...;` | Define a format | No `OTHER=` → unmapped values pass through raw (Rule 4) |
| `INVALUE` | `invalue name range1=val1 ...;` | Define an informat | Using where `VALUE` was meant; direction inversion |
| `PICTURE` | `picture name low-high='9,999.99' (prefix='$');` | Digit-selector numeric template | `9` vs `0` confusion on leading pads (Rule 8) |
| `CNTLIN=` | `proc format cntlin=ds; run;` | Build format from dataset | START / END length mismatch errors (Rule 5) |
| `CNTLOUT=` | `proc format cntlout=ds; run;` | Dump catalog to dataset for audit | Not specifying `LIBRARY=`; defaults to WORK |

## Silent Pitfalls

- **`VALUE` format with no `OTHER=`** — unmapped values pass through
  raw, mixing labels and codes in the output. See Rule 4.
- **CNTLIN START / END length mismatch** — an easy-to-miss data-prep
  error that yields an opaque PROC FORMAT error. See Rule 5.
- **PICTURE `9` vs `0`** — `9` is a required-digit selector that
  leaves blanks for absent positions; `0` forces leading-zero fill.
  Using the wrong one produces misaligned or mis-padded output. See
  Rule 8.
- **`CNTLOUT=` without `LIBRARY=`** — the audit dump lands in WORK
  and disappears at session end; specify a permanent library when
  archiving catalog state.

## Anti-patterns

**STOP** when you see any of the following:

- `value $grp 'A'='Alpha' 'B'='Beta';` with no `other=` and unmapped
  inputs expected to surface as `'Other'` → see Rule 4.
- `proc format cntlin=ds;` where `ds` lacks `FMTNAME` / `START` /
  `LABEL`, or has length-mismatched `START`/`END` → see Rule 5.
- `picture x low-high='999999999';` expecting leading zero fill on
  small numbers → use `0` selectors. See Rule 8.

See `put-vs-input.md` for trailing-dot rules on format references
and `../data-step/file-hygiene.md` for FORMAT-statement propagation.
