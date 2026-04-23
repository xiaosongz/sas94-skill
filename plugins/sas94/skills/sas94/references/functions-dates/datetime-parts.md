---
title: DATEPART, TIMEPART, and the datetime-vs-date distinction
loaded_when: '"DATEPART", "TIMEPART", "datetime vs date", "seconds since 1960", "SAS datetime", "YEAR on datetime", "extract date from datetime", "bridge datetime to date", or any datetime-conversion lookup.'
---

## Critical Rules

### Rule: SAS *date* is days since 01JAN1960; SAS *datetime* is **seconds** since 01JAN1960 00:00

The numeric scale differs by a factor of 86400. `YEAR`, `MONTH`,
`DAY`, `QTR`, `WEEKDAY`, `INTCK`, `INTNX` all expect a SAS *date*.
Passing a datetime does not raise an error — SAS interprets the
seconds-count as a day-count and returns a far-future-or-garbage
value. Always bridge through `DATEPART()` first.

```sas
/* CORRECT - bridge datetime to date before extracting */
data parts; set events;
  svc_dt  = datepart(service_dtm);
  svc_yr  = year(svc_dt);
  svc_mo  = month(svc_dt);
  svc_tod = timepart(service_dtm);
run;
```

```sas
/* WRONG - YEAR on a datetime returns year-of-seconds-since-1960 */
data parts; set events;
  svc_yr = year(service_dtm);   /* e.g. 4060-ish, silently wrong */
run;
```

### Rule: `TIMEPART(dt)` discards the date component silently

`TIMEPART` returns a SAS time (seconds since midnight) from a
datetime. If you store the result and later compare it to another
datetime, the comparison is nonsense because the date half is gone.
Treat the output as a time-of-day only.

```sas
/* CORRECT - time-of-day comparison only */
data after_hours; set events;
  tod = timepart(service_dtm);
  if tod >= '17:00't then after_hours = 1;
run;
```

```sas
/* WRONG - comparing timepart to a datetime */
data after_hours; set events;
  if timepart(service_dtm) >= cutoff_dtm then after_hours = 1;   /* scale mismatch */
run;
```

## Quick Ref

| Name | Syntax | Purpose | Common mistake |
|------|--------|---------|----------------|
| `DATEPART` | `datepart(dt)` | SAS date from SAS datetime | Omitting it and using YEAR(dt) directly — wrong |
| `TIMEPART` | `timepart(dt)` | SAS time from SAS datetime | Discards date info silently |

Detection: a numeric date-like column whose values are in the
billions (≈ `2.0e9` for year 2023) is a datetime; a column with
values around `23000` is a SAS date. `PROC CONTENTS` shows the format
(`DATETIME20.` vs `YYMMDD10.`) which is the most reliable indicator.

## Silent Pitfalls

- **YEAR / MONTH / DAY on a datetime** — SAS does not error; it
  interprets seconds-since-1960 as days-since-1960 and returns a
  garbage small integer. Always `DATEPART()` first.
- **INTCK / INTNX on a datetime** — same numeric-scale trap. The
  interval names `dtday`, `dtmonth`, `dtyear` are the datetime-aware
  variants; plain `'day'`, `'month'`, `'year'` expect SAS dates.
- **TIMEPART comparison to a datetime** — the result is a time-of-day
  (0..86399 seconds); comparing to a full datetime silently succeeds
  but is meaningless.
- **Stored-as-character datetime columns** — if a column is
  `CHAR(19)` with `2024-03-15T12:30:00`, neither `DATEPART` nor
  `YEAR` applies; bridge through `INPUT(str, e8601dt19.)` first.

## Anti-patterns

- `year(service_dtm)` / `month(service_dtm)` on a datetime column
  that was never bridged through `DATEPART()`.
- `intck('month', a_dtm, b_dtm)` — use `'dtmonth'` or datepart both
  sides.
- `format service_dtm yymmdd10.;` — the format is lying; the column
  is still seconds-scale.
- Comparing `timepart(a)` to `b` where `b` is a datetime.

See `construction.md` for `DHMS` to go the other direction (date +
time → datetime); see `intnx-intck.md` for the `dt*` interval
variants.
