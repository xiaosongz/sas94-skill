---
title: Date, time, and datetime construction functions
loaded_when: '"MDY", "DHMS", "TODAY", "DATE()", "TIME", "DATETIME function", "YEAR function", "MONTH function", "DAY function", "QTR", "WEEKDAY", "construct a date", "current date", "build a datetime", or any date/time construction lookup.'
---

## Critical Rules

### Rule: `MDY(m, d, y)` argument order is month-day-year, not ISO year-month-day

`MDY` takes three numeric arguments in US order. Passing
`mdy(2024, 3, 15)` compiles and returns a valid SAS date, but it is
`15MAR2024` interpreted as month=2024 (invalid → missing) or silently
shifted depending on values. Always pass literal month, day, year.

```sas
/* CORRECT - m, d, y */
data _null_;
  d = mdy(3, 15, 2024);         /* 15MAR2024 */
  put d= yymmdd10.;
run;
```

```sas
/* WRONG - ISO-style ordering */
data _null_;
  d = mdy(2024, 3, 15);          /* month=2024 -> missing */
run;
```

### Rule: `WEEKDAY(d)` returns 1=Sunday through 7=Saturday

Analysts coming from R (`lubridate::wday`), Python (`datetime.weekday`
uses 0=Monday), or ISO 8601 expect 1=Monday. SAS uses 1=Sunday. Any
"is-weekday" predicate must be spelled out explicitly.

```sas
/* CORRECT - explicit Monday..Friday set */
data flag; set claims;
  is_weekday = (weekday(service_dt) in (2,3,4,5,6));
run;
```

```sas
/* WRONG - assumes 1=Monday */
data flag; set claims;
  is_weekday = (weekday(service_dt) <= 5);   /* includes Sunday */
run;
```

## Canonical Idiom: ISO-formatted run-date stamp via `%SYSFUNC(today(), ...)`

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

## Quick Ref

| Name | Syntax | Purpose | Common mistake |
|------|--------|---------|----------------|
| `TODAY` | `today()` | Current date (SAS date integer) | Embeds wall-clock — breaks reproducibility |
| `DATE` | `date()` | Alias for `today()` | Same reproducibility issue |
| `TIME` | `time()` | Seconds since midnight | Type is SAS time, not datetime |
| `DATETIME` | `datetime()` | Current SAS datetime value | Seconds since 01JAN1960 00:00 — not Unix epoch |
| `MDY` | `mdy(m, d, y)` | Construct SAS date from m/d/y | Argument order is m-d-y (not ISO y-m-d) |
| `DHMS` | `dhms(d, h, m, s)` | Compose datetime from d/h/m/s | Passing a datetime as the date arg |
| `YEAR` | `year(d)` | Extract year from SAS date | Passing a datetime silently returns year-of-1960 offset |
| `MONTH` | `month(d)` | Extract month 1..12 from SAS date | Same datetime confusion as YEAR |
| `DAY` | `day(d)` | Extract day-of-month 1..31 | Same datetime confusion as YEAR |
| `QTR` | `qtr(d)` | Quarter 1..4 | SAS calendar quarters, not fiscal |
| `WEEKDAY` | `weekday(d)` | Day-of-week 1..7 (1=Sunday) | Many analysts expect 1=Monday |

`DHMS(d, h, m, s)` composes a SAS datetime from a SAS *date* plus
hour/minute/second. Passing a datetime as the first argument
double-counts the epoch offset.

## Silent Pitfalls

- **TODAY / DATE / DATETIME embed wall-clock time** — programs that
  use these for dataset names or cutoff logic are non-reproducible.
  Accept a `&asof_dt` macro parameter with a default of
  `today()` so reruns can pin the date.
- **WEEKDAY returns 1=Sunday, 7=Saturday** — analysts coming from R
  / Python / ISO week numbering expect 1=Monday. Guard any
  `if weekday(d) in (2,3,4,5,6)` "is weekday" predicate explicitly.
- **MDY takes m-d-y, not y-m-d** — ISO-style `mdy(2024, 3, 15)`
  produces a missing value silently.
- **QTR returns calendar quarters** — for fiscal-year reporting
  where Q1 starts in April or July, subtract an offset before calling
  `QTR` or build the mapping with a format.

## Anti-patterns

- Hard-coded `today()` in dataset names or cutoff logic without a
  `&asof_dt` override → reruns produce different output.
- `if weekday(d) <= 5` as an "is-weekday" test — silently includes
  Sunday.
- `mdy(year, month, day)` copied from ISO-conditioned code.
- `dhms(my_datetime, 0, 0, 0)` — pass a SAS date, not a datetime.

See `datetime-parts.md` for extracting parts from datetime values;
see `intnx-intck.md` for shifting the constructed dates.
