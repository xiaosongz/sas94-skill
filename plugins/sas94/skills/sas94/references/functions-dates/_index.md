---
title: Date and time function reference — index
loaded_when: '"date arithmetic", "INTNX", "INTCK", "TODAY", "DATE", "DATEPART", "TIMEPART", "DATETIME", "MDY", "DHMS", "DATDIF", "date function", or any date/time/datetime function lookup without a more specific trigger.'
---

## Routing

| Atom | Load when you need |
|------|--------------------|
| `intnx-intck.md` | `INTNX` alignment (`'b'`/`'e'`/`'m'`/`'s'`), `INTCK` boundary counting, month-end / start-of-month shifts, anniversary reconstruction, boundary-vs-duration footgun |
| `construction.md` | Building a date from parts (`MDY`, `DHMS`), current wall-clock (`TODAY`, `DATE`, `TIME`, `DATETIME`), extracting calendar pieces from a SAS *date* (`YEAR`, `MONTH`, `DAY`, `QTR`, `WEEKDAY`), `%SYSFUNC(today(), ...)` macro bridge |
| `datetime-parts.md` | `DATEPART`, `TIMEPART`, the days-vs-seconds-since-1960 distinction, bridging a datetime into date-scale functions, `'dtmonth'` / `'dtyear'` interval variants |
| `date-arithmetic.md` | Subtracting dates or datetimes, "add one month" via `INTNX` vs naive `+30`, `DATDIF` financial day counts, `YRDIF` age calculation |

## One-line summaries

- **`intnx-intck.md`** — `INTNX` default alignment is `BEGINNING`
  (not `SAME`); `INTCK` counts boundary crossings (not elapsed
  duration). Both are the #1 source of silent claims-pipeline bugs.
- **`construction.md`** — `MDY` is month-day-year (not ISO); `WEEKDAY`
  is 1=Sunday (not 1=Monday); `TODAY`/`DATETIME` embed wall-clock
  time and break reproducibility.
- **`datetime-parts.md`** — SAS date is days-since-1960, SAS datetime
  is *seconds*-since-1960 (86400x scale difference). `YEAR(dtm)` on a
  datetime silently returns garbage; always `DATEPART()` first.
- **`date-arithmetic.md`** — Date subtraction yields days; datetime
  subtraction yields seconds. "Add one month" is `INTNX('month', d,
  1, 'same')`, never `+ 30`. `DATDIF` needs an explicit basis.

## Common cross-references

- String parsing of date-like columns (`INPUT(str, yymmdd10.)`): see
  prose in `construction.md`; for the full function family consult
  the strings reference.
- Attaching a date format to a variable (`FORMAT d yymmdd10.;`):
  `../data-step/retain-pdv.md` for PDV-level format assignment;
  `../formats-informats/date-formats.md` for the format catalogue.
- `%SYSFUNC(today(), yymmddn8.)` macro bridge: inline idiom in
  `construction.md`; `../macros/sysfunc-and-eval.md` for the general
  pattern.
- ISO-format round-trips and `PUT d yymmdd10.` vs
  `INPUT(s, yymmdd10.)`: `../formats-informats/put-vs-input.md` and
  `../formats-informats/date-formats.md`.
