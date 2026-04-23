---
title: put() vs input() — direction rule and trailing dot
loaded_when: '"put(", "input(", "putn", "putc", "inputn", "inputc", "FORMAT statement", "INFORMAT statement", "trailing dot", or any direction-conversion / run-time format-name task.'
---

## Critical Rules

### Rule 1: `put()` goes variable → string; `input()` goes string → variable — inverting them silently returns wrong values

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

### Rule 6: FORMAT (display) and INFORMAT (parse) are distinct attributes — using `FORMAT` where `INFORMAT` is needed silently reads garbage

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

## Quick Ref

| Name | Syntax | Purpose | Common mistake |
|------|--------|---------|----------------|
| `FORMAT` stmt | `format var fmt.;` | Attach display format to variable | No trailing dot on reference (Rule 2) |
| `INFORMAT` stmt | `informat var fmt.;` | Attach parse informat to variable | Using `FORMAT` instead; silent parse failure (Rule 6) |
| `put()` | `str = put(num, fmt.);` | Numeric / char → formatted string | Applying to already-character input (Rule 1) |
| `input()` | `num = input(str, infmt.);` | String → numeric / date / time | Using `put()` by mistake (Rule 1) |
| `putn()` / `putc()` | `str = putn(num, 'mmddyy10.');` | Format name supplied as run-time string | Forgetting the name must end in `.` inside the string |
| `inputn()` / `inputc()` | `num = inputn(str, 'mmddyy10.');` | Informat name supplied as run-time string | Forgetting the trailing `.` |

## Silent Pitfalls

- **`put()` / `input()` inversion** — `put()` formats a stored value
  for display; `input()` parses an input string. Swapping them
  silently returns wrong values (or triggers a type-mismatch NOTE
  that gets buried in log noise). See Rule 1.
- **Missing trailing dot on format reference** — `format age agegrp;`
  with no dot makes SAS look for a variable named `agegrp`. See
  Rule 2.
- **`FORMAT` used where `INFORMAT` is needed** — SAS parses with
  default `w.d` and produces missings or garbage, then displays the
  garbage with the attached FORMAT. See Rule 6.
- **`putn` / `inputn` with a dot-less name string** — the first
  argument is a string literal that itself needs the trailing dot
  (`'mmddyy10.'`, not `'mmddyy10'`); omission is a silent failure.

## Anti-patterns

**STOP** when you see any of the following — the code runs but the
values are almost certainly not what the author meant:

- `put(char_var, mmddyy10.)` or `input(num_var, best.)` — direction
  inversion. See Rule 1.
- `format dob mmddyy10` (no trailing dot) → SAS searches for
  variable `mmddyy10`. See Rule 2.
- DATA step with `format date mmddyy10.;` but no `informat`, reading
  a text column → see Rule 6.

See `../data-step/file-hygiene.md` for where and when attached
FORMAT / INFORMAT / LENGTH / ATTRIB propagate to the output dataset.
