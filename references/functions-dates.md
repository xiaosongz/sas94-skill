---
title: SAS date and time function reference
scope: Date/time/datetime function cheatsheet — INTNX, INTCK, TODAY, MDY, DATEPART, TIMEPART, DHMS, YEAR/MONTH/DAY/QTR/WEEKDAY, DATDIF. Focused on the INTNX alignment default and other argument-order traps that produce silent bugs in claims pipelines.
loaded_when: '"date arithmetic", "INTNX", "INTCK", "TODAY", "DATE", "DATEPART", "TIMEPART", "DATETIME", "MDY", "DHMS", "DATDIF", or any date/time/datetime function lookup.'
last_reviewed: 2026-04-22
reviewer: xiaosongz
---

## Overview

Date and datetime functions are where claims-pipeline logic silently
loses a month or a day. `INTNX('month', dt, 0)` returns the first of
the month, not `dt` — the default fourth argument is `BEGINNING`.
`YEAR(datetime_value)` returns an offset from 1960 because SAS
datetimes are seconds since 01JAN1960 while `YEAR` expects a SAS
*date* (days). This file covers interval arithmetic (`INTCK`, `INTNX`),
construction (`MDY`, `DHMS`, `TODAY`, `DATE`, `TIME`, `DATETIME`),
extraction (`YEAR`, `MONTH`, `DAY`, `QTR`, `WEEKDAY`, `DATEPART`,
`TIMEPART`), and day-count (`DATDIF`). Every rule and idiom
cites the `SAS Functions and CALL Routines: Reference` docset
(`lefunctionsref`).

For string and numeric functions see `functions-strings.md` and
`functions-numeric.md`. For DATA-step `FORMAT` / `LENGTH` / `ATTRIB`
statements see `data-step.md`; for `%SYSFUNC(today(), ...)` see
`macros.md`.

## Critical Rules

### Rule 1: `INTNX('interval', dt, 0)` with no `alignment` returns the **beginning** of the interval, not `dt` — use `'S'` (SAME) for same-day alignment

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm

The fourth argument `alignment` defaults to `BEGINNING`. So
`intnx('month', service_dt, 0)` returns the first of `service_dt`'s
month, not `service_dt` itself. For "shift by N months but keep the
day-of-month" semantics use `'SAME'` (alias `'S'`). A common claims
bug: computing `months_since_start = intck('month', a, b)` and then
trying to reconstruct the corresponding date with `intnx('month', a,
k)` — which lands on the first of each month, not the anniversary day.

```sas
/* CORRECT - SAME alignment preserves day-of-month */
data claims; set claims;
  anniversary = intnx('year', enroll_dt, 1, 'same');
run;
```

```sas
/* WRONG - default BEGINNING alignment; lands on 01JAN */
data claims; set claims;
  anniversary = intnx('year', enroll_dt, 1);   /* not what the name suggests */
run;
```

## Canonical Idioms

### Idiom: Month-end alignment for claims billing cycles

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm

Purpose: map every service date to the end of its calendar month for
PMPM / member-month aggregation. Use `INTNX` with `'E'` (END)
alignment — the last-day-of-month adjustment handles February and
leap years automatically, so there's no special case for 30- vs
31-day months.

```sas
data claims_eom; set claims;
  bill_eom   = intnx('month', service_dt, 0, 'e');   /* E = end-of-month */
  bill_start = intnx('month', service_dt, 0, 'b');   /* B = start-of-month */
run;
```

### Idiom: ISO-formatted run-date stamp via `%SYSFUNC(today(), ...)`

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm

Purpose: get today's date into a macro variable for dataset-name or
filepath stamping, without a `DATA _NULL_` round-trip. The second
argument of `%SYSFUNC` is a format; pairing `today()` with
`yymmddn8.` produces an 8-digit ISO stamp (`20260422`) safe for
dataset names. Watch for functions whose arguments contain commas
(`SCAN`, `SUBSTR`, `CATX`) when crossing into macro context — the
inner commas need `%str(,)` masking.

```sas
/* run-date stamp for a dataset name */
%let rundate = %sysfunc(today(), yymmddn8.);
data claims_&rundate; set claims; run;
```

## Function / Statement Quick Ref

| Name | Syntax | Purpose | Common mistake | Doc URL |
|------|--------|---------|----------------|---------|
| `INTCK` | `intck('interval', d1, d2 <, 'method'>)` | Count interval boundaries between two dates | Default `method='DISCRETE'` counts boundaries; use `'CONTINUOUS'` for anniversary semantics | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| `INTNX` | `intnx('interval', d, n <, 'align'>)` | Shift date by N intervals | Default align=`'BEGINNING'`; use `'S'` for same-day (see Rule 1) | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| `TODAY` | `today()` | Current date (SAS date integer) | Embeds wall-clock — breaks reproducibility | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| `DATE` | `date()` | Alias for `today()` | Same reproducibility issue | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| `TIME` | `time()` | Seconds since midnight | Type is SAS time, not datetime | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| `DATETIME` | `datetime()` | Current SAS datetime value | Seconds since 01JAN1960 00:00 — not Unix epoch | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| `YEAR` | `year(d)` | Extract year from SAS date | Passing a datetime silently returns year-of-1960 offset | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| `MONTH` | `month(d)` | Extract month 1..12 from SAS date | Same datetime confusion as YEAR | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| `DAY` | `day(d)` | Extract day-of-month 1..31 | Same datetime confusion as YEAR | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| `QTR` | `qtr(d)` | Quarter 1..4 | SAS calendar quarters, not fiscal | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| `WEEKDAY` | `weekday(d)` | Day-of-week 1..7 (1=Sunday) | Many analysts expect 1=Monday | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| `MDY` | `mdy(m, d, y)` | Construct SAS date from m/d/y | Argument order is m-d-y (not ISO y-m-d) | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| `DATEPART` | `datepart(dt)` | SAS date from SAS datetime | Omitting it and using YEAR(dt) directly — wrong | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| `TIMEPART` | `timepart(dt)` | SAS time from SAS datetime | Discards date info silently | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| `DHMS` | `dhms(d, h, m, s)` | Compose datetime from d/h/m/s | Passing a datetime as the date arg | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |
| `DATDIF` | `datdif(d1, d2, basis)` | Day-count with basis ('ACT/ACT', '30/360') | Basis is required; not like INTCK('day') | [`lefunctionsref`](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm) |

## Silent Pitfalls

All pitfalls below share the same source:
https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm

- **INTNX default alignment is `BEGINNING`** — `intnx('month', dt, 0)`
  is the first of the month, not `dt`. Every `INTNX` call in a claims
  pipeline should carry an explicit alignment argument. See Rule 1.

- **YEAR / MONTH / DAY on a datetime** — SAS does not error; it
  interprets seconds-since-1960 as days-since-1960 and returns a
  garbage small integer. Always `DATEPART()` first.

- **WEEKDAY returns 1=Sunday, 7=Saturday** — analysts coming from R
  / Python / ISO week numbering expect 1=Monday. Guard any
  `if weekday(d) in (2,3,4,5,6)` "is weekday" predicate explicitly.

- **TODAY / DATE / DATETIME embed wall-clock time** — programs that
  use these for dataset names or cutoff logic are non-reproducible.
  Accept a `&asof_dt` macro parameter with a default of
  `today()` so reruns can pin the date.

## Anti-patterns (STOP signs)

**STOP** when you see any of the following — the code compiles and
produces output, but the output is almost certainly wrong:

- `intnx('month', d, n)` with no fourth argument when you meant
  "same-day n months later" → see Rule 1.
- `year(service_dtm)` / `month(service_dtm)` on a datetime column
  that was never bridged through `DATEPART()` → Silent Pitfalls.
- Hard-coded `today()` in dataset names or cutoff logic without a
  `&asof_dt` override → Silent Pitfalls.

## See Also

- [functions-strings.md](functions-strings.md) — string-handling
  functions (SCAN, SUBSTR, CATX, COMPRESS, TRANWRD, INDEX, FIND) and
  date-string parsing.
- [functions-numeric.md](functions-numeric.md) — numeric and array
  functions (SUM, ROUND, MOD, DIM) often combined with date arithmetic.
- [formats-informats.md](formats-informats.md) — date/time formats
  used with `PUT` after `INTNX` / `MDY` / `TODAY`; ISO-format
  round-trips.
- [data-step.md](data-step.md) — `FORMAT` / `LENGTH` / `ATTRIB`
  statements that attach date formats to variables.
- [macros.md](macros.md) — `%SYSFUNC(today(), ...)` bridge and
  macro-context date arithmetic.
- [SAS Functions and CALL Routines: Reference](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=lefunctionsref&docsetTarget=titlepage.htm)
