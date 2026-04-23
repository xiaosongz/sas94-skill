---
title: ODS destinations (RTF / PDF / EXCEL / HTML)
loaded_when: '"ODS RTF", "ODS EXCEL", "ODS PDF", "ODS HTML", "ods _all_ close", "style=journal", "sheet_name", "multi-sheet excel", "rtf report", "pdf report", routing PROC output to a file destination, or any destination open/close/options task.'
---

## Critical Rules

### Rule: Every `ODS destination FILE=...` must be paired with a matching `ODS destination CLOSE;`

An ODS destination opened with `FILE=` stays open for the rest of
the SAS session until you close it. Subsequent procs continue to
append; a second `ODS RTF FILE=` pointing at the same path
silently reopens with an incomplete RTF on disk; a failed job
leaves a half-written RTF that Word cannot parse. The canonical
idempotent wrapper is `ods listing close; ods rtf file='...'; PROCs; ods rtf close; ods listing;`. If you lose track of what's
open, `ods _all_ close;` resets every destination.

```sas
/* CORRECT - symmetric open / close bracket around the procs */
ods listing close;
ods rtf file="report.rtf" style=journal;
proc freq data=claims; tables dx_code; run;
proc means data=claims; var paid_amt; run;
ods rtf close;
ods listing;
```

```sas
/* WRONG - forgotten close; next batch run appends to the same file */
ods rtf file="report.rtf";
proc freq data=claims; tables dx_code; run;
/* no ods rtf close; here - file never flushed cleanly */
```

### Rule: Destination options set at `ODS dest FILE=...` are global — nest `ODS dest OPTIONS(...)` between procs to change them per-PROC

Opening an RTF / EXCEL / PDF destination applies the file-level
options (style, bodytitle, embedded_titles, etc.) to every PROC
until the destination closes. Per-proc options like Excel sheet
names live on `ODS EXCEL OPTIONS(SHEET_NAME='...')`, which you
re-issue before each PROC you want to rename. A single `ODS EXCEL`
open with no inter-proc `OPTIONS` lets SAS auto-name sheets
(`Sheet1`, `Sheet2`) — usually not what was intended.

```sas
/* CORRECT - per-proc sheet_name inside one open EXCEL destination */
ods excel file="claims_report.xlsx" style=journal;

ods excel options(sheet_name="Enrollment");
proc freq data=enroll; tables plan_type; run;

ods excel options(sheet_name="Costs");
proc means data=costs; var paid_amt; run;

ods excel close;
```

```sas
/* WRONG - no sheet_name updates; Excel names them Sheet1/Sheet2 */
ods excel file="claims_report.xlsx";
proc freq data=enroll; tables plan_type; run;
proc means data=costs; var paid_amt; run;
ods excel close;
```

### Rule: `ODS _ALL_ CLOSE;` is the reset — use it at the top of a production script to guarantee clean state

`ods _all_ close;` closes every currently open destination in one
statement. In an interactive session, a prior run may have left
RTF / EXCEL open; a new script then silently appends to them. Put
`ods _all_ close;` followed by `ods listing;` at the top of
production / batch code to start from a known state. The trade-off:
if you forget to reopen a destination before the next PROC, nothing
is captured anywhere — which is usually better than silent append.

```sas
/* CORRECT - reset then deliberately open what you need */
ods _all_ close;
ods listing;
ods rtf file="report.rtf" style=journal;
proc freq data=claims; tables dx_code; run;
ods rtf close;
```

```sas
/* WRONG - implicit carryover from a previous interactive session */
ods rtf file="report.rtf";  /* previous RTF may still be open! */
proc freq data=claims; tables dx_code; run;
ods rtf close;
```

## Canonical Idioms

### Route a suite of PROCs to a single RTF report with `STYLE=`

The canonical claims-reporting pattern — several descriptive
PROCs landing in one Word-openable RTF. `STYLE=journal` is the
clean, print-ready default; `STYLE=minimal` strips most colors for
black-and-white printing. Close `ODS LISTING` first to avoid a
duplicate `.lst`.

```sas
ods listing close;
ods rtf file="claims_monthly_report.rtf" style=journal;
title "Monthly Claims Summary";

proc freq data=claims;
  tables dx_code * plan_type / missing;
run;

proc means data=claims n mean median min max;
  class plan_type;
  var paid_amt days_supply;
run;

proc print data=top10_dx noobs label;
  var dx_code description count pct;
run;

title;
ods rtf close;
ods listing;
```

### Multi-sheet Excel with per-PROC sheet naming

The deliverable-to-a-clinician pattern — one xlsx with Enrollment,
Costs, Utilization tabs. Re-issue
`ods excel options(sheet_name='...')` before every PROC you want
on its own tab; `sheet_interval='proc'` (the default) makes each
PROC start a new sheet.

```sas
ods excel file="claims_dashboard.xlsx" style=analysis
  options(sheet_interval='proc');

ods excel options(sheet_name="Enrollment");
proc freq data=enroll; tables plan_type; run;

ods excel options(sheet_name="Costs");
proc means data=costs n sum mean;
  class plan_type;
  var paid_amt;
run;

ods excel options(sheet_name="Utilization");
proc freq data=claims; tables dx_code / out=dx_freq; run;

ods excel close;
```

## Quick Ref

| Name | Syntax | Purpose | Common mistake |
|------|--------|---------|----------------|
| `ODS RTF` | `ods rtf file='f.rtf' style=journal;` | Open RTF (Word) destination | Forgetting `ODS RTF CLOSE;` |
| `ODS EXCEL` | `ods excel file='f.xlsx' options(sheet_interval='proc');` | Open Excel (native xlsx) destination | No per-proc `sheet_name`; sheets named `Sheet1`... |
| `ODS PDF` | `ods pdf file='f.pdf' style=journal;` | Open PDF destination | Omitting `STYLE=` → default often has color backgrounds |
| `ODS HTML` | `ods html file='f.html' path='out';` | Open HTML destination | Not setting `PATH=`; files scatter in working dir |
| `ODS _ALL_ CLOSE` | `ods _all_ close;` | Close every open destination | Calling mid-pipeline then forgetting to reopen one |
| `dest OPTIONS(...)` | `ods excel options(sheet_name='x');` | Per-PROC destination option update | Setting only on `FILE=` and expecting per-sheet rename |

## Silent Pitfalls

- **Forgotten `ODS dest CLOSE;`** — an open destination continues
  to receive output from every subsequent PROC in the session.
  Interactive sessions are especially prone to this.
- **Excel auto-named sheets** — one `ODS EXCEL FILE=...` with no
  inter-proc `OPTIONS(SHEET_NAME=...)` gives Sheet1, Sheet2, etc.
- **Session-state carryover** — a previous interactive run may
  have left RTF / EXCEL open; a new `ODS RTF FILE=` silently
  re-opens and appends.

## Anti-patterns

- `ODS RTF FILE=...;` with no matching `ODS RTF CLOSE;` at the end
  of the script. Subsequent procs append silently.
- `ODS EXCEL FILE=...;` followed by two PROCs with no inter-proc
  `SHEET_NAME=`. Auto-named sheets result.
- Long-running session that accumulates open destinations across
  interactive edits — fix with `ODS _ALL_ CLOSE;`.

For the `ODS LISTING` close-before-RTF discipline see `ods-listing.md`; for narrowing a destination to a subset of tables see `ods-select-exclude.md`.
