---
title: Date / time / datetime formats and informats
loaded_when: '"mmddyy", "yymmdd", "date9", "datetime", "anydtdte", "DATESTYLE", "date informat", "date format", "parse date", or any date / time / datetime column read or display.'
---

## Critical Rules

### Rule 3: `anydtdte.` resolves ambiguous dates using the `DATESTYLE=` system option — set it explicitly

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

## Canonical Idioms

### Parse a messy date column with `anydtdte.` plus explicit `DATESTYLE=`

Claims extracts often arrive with heterogeneous date strings
across vendors (`01/15/2024`, `2024-01-15`, `15JAN2024`).
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

## Quick Ref

| Name | Syntax | Purpose | Common mistake |
|------|--------|---------|----------------|
| `mmddyy10.` | `format dob mmddyy10.;` | US-style `MM/DD/YYYY` date display | Confusing with informat direction |
| `yymmdd10.` | `format dob yymmdd10.;` | ISO-style `YYYY-MM-DD` display | Width 8 drops century digits |
| `date9.` | `format dob date9.;` or `'15MAR2024'd` | Display + date-literal form (`DDMONYYYY`) | Using `date7.` — drops century digits |
| `datetime20.` | `format ts datetime20.;` | Date + time display | Confusing with `date` informat (strips time) |
| `anydtdte.` | `dt = input(s, anydtdte32.);` | Permissive date informat | Missing `DATESTYLE=` (Rule 3) |
| `options datestyle=` | `options datestyle=mdy;` | Pin ambiguous-date interpretation | Leaving default; host locale varies (Rule 3) |

## Informat vs format pairing

Reading a date column from raw text requires BOTH an informat (to
parse) and a format (to display). The informat converts the CSV
cell `'03/15/2024'` into the SAS date number `23451`; the format
converts `23451` back into a human-readable `'03/15/2024'` on PROC
PRINT. Pair them in the DATA step:

```sas
data visits;
  infile 'visits.csv' dsd;
  informat srvc_date mmddyy10.;   /* parse */
  format   srvc_date mmddyy10.;   /* display */
  input patient_id srvc_date paid_amt;
run;
```

Omitting the informat reparses the column with the default numeric
informat and yields missing or garbage; see `put-vs-input.md` Rule 6.

## Silent Pitfalls

- **`anydtdte.` with locale-defaulted `DATESTYLE`** — same input
  string parses to a different date on US vs EU hosts. Always set
  `options datestyle=mdy;` explicitly. See Rule 3.
- **`yymmdd8.` / `date7.` width drops century** — the 8-char
  `YYMMDD` variant truncates to 2-digit year; always prefer
  `yymmdd10.` and `date9.`.
- **`datetime20.` vs `date9.` mix-up** — a datetime variable
  formatted with `date9.` shows the date only (seconds still
  stored); the reverse silently reads zero time.
- **Unquoted date literals** — SAS date literals need the `d` / `t`
  / `dt` suffix and quotes: `'15MAR2024'd`, `'12:34:56't`,
  `'15MAR2024:12:34:56'dt`. Missing the suffix makes it a string.

## Anti-patterns

**STOP** when you see any of the following:

- `input(s, anydtdte10.)` with no `options datestyle=` → host-locale
  silent divergence. See Rule 3.
- `format dob date7.;` on modern data → century digits get dropped.
- Parsing a date column with `format` but no `informat` → see
  `put-vs-input.md` Rule 6.

Date arithmetic helpers (`INTCK`, `INTNX`, `MDY`, `DATEPART`) live
in the functions reference (being split in parallel).
