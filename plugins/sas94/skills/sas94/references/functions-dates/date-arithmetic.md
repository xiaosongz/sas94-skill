---
title: Date arithmetic, day counts, and "add one month" patterns
loaded_when: '"date arithmetic", "subtract dates", "add days", "days between", "DATDIF", "add one month", "date difference", "age in years", or any date-math lookup.'
---

## Critical Rules

### Rule: Subtracting two SAS dates yields a **day count**; subtracting two SAS datetimes yields a **second count**

Because date is days-since-1960 and datetime is seconds-since-1960,
naive subtraction produces wildly different scales. For datetimes,
divide by 86400 to get days, or bridge both sides through `DATEPART`
before subtracting.

```sas
/* CORRECT */
data los; set stays;
  los_days = discharge_dt - admit_dt;                  /* dates: days */
  los_days_dtm = (discharge_dtm - admit_dtm) / 86400;  /* datetimes: seconds/86400 */
run;
```

```sas
/* WRONG - datetime subtraction gives seconds, misread as days */
data los; set stays;
  los_days = discharge_dtm - admit_dtm;   /* ~86400x too large */
run;
```

### Rule: "Add one month" is **not** `+ 30` — use `INTNX('month', d, 1, 'same')`

Adding a fixed number of days walks past month-ends unpredictably
(February, 30- vs 31-day months, leap years). `INTNX` with `'same'`
alignment handles month-length variation automatically. When the
source day-of-month does not exist in the target month (e.g. Jan 31 +
1 month), `INTNX` clamps to the last valid day of the target month.

```sas
/* CORRECT - INTNX handles month length and leap years */
data followup; set enroll;
  next_visit = intnx('month', enroll_dt, 1, 'same');
run;
```

```sas
/* WRONG - naive +30 slides the calendar */
data followup; set enroll;
  next_visit = enroll_dt + 30;   /* drifts ~5 days/year */
run;
```

### Rule: `DATDIF(d1, d2, basis)` requires an explicit basis and is **not** equivalent to `INTCK('day', ...)`

`DATDIF` is a financial day-count with basis `'ACT/ACT'` (actual) or
`'30/360'` (bond-style). It treats months as 30 days under
`'30/360'`, which differs from a calendar day count. Use it only for
financial calculations; for plain calendar-day gaps use subtraction
or `INTCK('day', ...)`.

```sas
/* CORRECT - financial day count for a bond */
data coupons; set bonds;
  bond_days = datdif(issue_dt, settle_dt, '30/360');
  cal_days  = settle_dt - issue_dt;            /* calendar days */
run;
```

```sas
/* WRONG - DATDIF without thinking about basis */
data gap; set claims;
  gap = datdif(admit_dt, discharge_dt);   /* syntax error - basis required */
run;
```

## Canonical Idiom: Age in years as of a reference date

Purpose: compute integer age using `YRDIF` with the `'AGE'` basis,
which handles leap years and the birthday-not-yet-reached case
correctly. Truncate with `FLOOR` for integer age.

```sas
data cohort; set members;
  age_yrs = floor(yrdif(birth_dt, asof_dt, 'AGE'));
run;
```

## Quick Ref

| Name | Syntax | Purpose | Common mistake |
|------|--------|---------|----------------|
| `DATDIF` | `datdif(d1, d2, basis)` | Day-count with basis ('ACT/ACT', '30/360') | Basis is required; not like INTCK('day') |
| `YRDIF` | `yrdif(d1, d2, basis)` | Year fraction with basis ('AGE', 'ACT/ACT', '30/360') | Use `'AGE'` for calendar age |
| `d2 - d1` | date arithmetic | Calendar days between SAS dates | Returns seconds for datetimes |

Patterns:

- Days between dates: `d2 - d1`.
- Days between datetimes: `(dt2 - dt1) / 86400`, or
  `datepart(dt2) - datepart(dt1)`.
- Calendar month shift: `intnx('month', d, n, 'same')`.
- End-of-month of next month: `intnx('month', d, 1, 'e')`.

## Silent Pitfalls

- **Datetime subtraction in seconds misread as days** — the number is
  large (86400x) and looks like "a lot of days". Divide or bridge via
  `DATEPART`.
- **`+ 30` as "add one month"** — drifts across month boundaries;
  breaks in February. Use `INTNX('month', d, 1, 'same')`.
- **Day-of-month clamping with INTNX `'same'`** — Jan 31 + 1 month
  returns Feb 28/29, not Mar 3. This is usually what you want, but
  round-tripping is lossy.
- **DATDIF vs subtraction** — `datdif(d1, d2, '30/360')` is a bond
  day count, not calendar days; the results differ at month-end.

## Anti-patterns

- `discharge_dtm - admit_dtm` stored as `los_days` without dividing
  by 86400.
- `enroll_dt + 30` (or `+ 365`) as "one month" / "one year" later.
- `datdif(a, b, 'ACT/ACT')` used when plain `b - a` was intended.
- Computing age as `year(asof) - year(birth)` — ignores whether the
  birthday has passed; use `floor(yrdif(birth, asof, 'AGE'))`.

See `intnx-intck.md` for the alignment argument semantics that this
file depends on; see `datetime-parts.md` for the date-vs-datetime
scale distinction.
