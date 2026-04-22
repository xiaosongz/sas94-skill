---
title: ODS and output reference
scope: ODS RTF / EXCEL / PDF / HTML destinations, `ODS OUTPUT` capture of proc tables as datasets, `ODS GRAPHICS`, `ODS EXCLUDE` / `ODS SELECT` scoping, destination open/close discipline, and `ODS TRACE` for discovering table names.
loaded_when: '"ODS RTF", "ODS EXCEL", "ODS PDF", "ODS HTML", "ODS OUTPUT", "ODS GRAPHICS", "ODS TRACE", "ods _all_ close", routing PROC output to a file, capturing a proc table as a dataset, or any output-delivery / reporting task.'
last_reviewed: 2026-04-22
reviewer: xiaosongz
---

## Overview

The Output Delivery System (ODS) is the SAS layer that decides what
happens to the tabular and graphical output a procedure produces.
Every PROC emits a stream of named output objects (ParameterEstimates,
FitStatistics, OneWayFreqs, ...); ODS routes that stream to one or
more open destinations — RTF, EXCEL, PDF, HTML, LISTING, or the
special OUTPUT destination that turns output objects into SAS
datasets. A destination opened with `ODS RTF FILE=...` stays open
until explicitly closed, so every subsequent PROC in the session
appends to it. That statefulness is where most ODS bugs come from:
the pipeline script opens an RTF, the PROC works, nothing shows up
because the previous run never ran `ODS RTF CLOSE`.

The two workhorse patterns are (1) route a block of PROCs to an
RTF / Excel / PDF report and (2) capture a single proc's named table
as a SAS dataset for downstream analysis. Both are concise when the
destination names and output-object names are right and silent or
empty when they aren't. `ODS TRACE ON;` is the canonical discovery
tool — it writes every output object's path and label to the log,
and `ODS OUTPUT Table=ds;` consumes those names directly. This file
encodes the rules from the SAS Output Delivery System: User's Guide
(odsug) and the Base SAS Procedures Guide (proc) chapters on ODS
OUTPUT and ODS destinations.

See also `base-procs.md` for `NOPRINT` as an alternative when you
only want an OUTPUT dataset, and `stat-procs.md` for the common
ODS OUTPUT captures (ParameterEstimates, FitStatistics, etc.) used
in modeling pipelines.

## Contents

- [Critical Rules](#critical-rules)
- [Canonical Idioms](#canonical-idioms)
- [Function / Statement Quick Ref](#function--statement-quick-ref)
- [Silent Pitfalls](#silent-pitfalls)
- [Anti-patterns (STOP signs)](#anti-patterns-stop-signs)
- [See Also](#see-also)

## Critical Rules

### Rule 1: Every `ODS destination FILE=...` must be paired with a matching `ODS destination CLOSE;`

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=odsug&docsetTarget=titlepage.htm

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

### Rule 2: `ODS OUTPUT Table=ds;` requires the exact ODS table name — discover it with `ODS TRACE ON;`

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=odsug&docsetTarget=titlepage.htm

`ODS OUTPUT ParameterEstimates=pe;` captures the proc's named
output object as a SAS dataset. Mis-type the table name and you
get a silently empty dataset — no error, no warning, just zero
rows. Run the proc once under `ods trace on;` to print every
object's path and label to the log, then match the name exactly
(case-insensitive, but spelling must match). `ODS TRACE OFF;`
afterward to stop flooding the log.

```sas
/* CORRECT - discover the table name, then capture it */
ods trace on;
proc logistic data=claims; model outcome = age sex; run;
ods trace off;
/* log shows Name: ParameterEstimates, Name: FitStatistics, etc. */

ods output ParameterEstimates=lr_pe
           FitStatistics=lr_fit;
proc logistic data=claims; model outcome = age sex; run;
```

```sas
/* WRONG - misspelled name silently produces zero rows in lr_pe */
ods output ParamEstimates=lr_pe;
proc logistic data=claims; model outcome = age sex; run;
/* lr_pe exists but has 0 observations; no message about the miss */
```

### Rule 3: `ODS SELECT` / `ODS EXCLUDE` controls which output objects a destination receives — default is SELECT ALL for everything except the OUTPUT destination

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=odsug&docsetTarget=titlepage.htm

Every open destination maintains a selection list. The default is
`SELECT ALL` for RTF / EXCEL / PDF / HTML / LISTING — every output
object the proc emits goes through. The OUTPUT destination starts
at `EXCLUDE ALL` — nothing becomes a dataset until you name it via
`ODS OUTPUT ...`. To gate a destination to a single table, use
`ods rtf select ParameterEstimates;` before the proc; list resets
at the next PROC step unless you add `PERSIST=PROC`.

```sas
/* CORRECT - RTF gets only the ParameterEstimates table */
ods rtf file="lr_params.rtf";
ods rtf select ParameterEstimates;
proc logistic data=claims; model outcome = age sex; run;
ods rtf close;
```

```sas
/* WRONG - RTF gets every default panel; the file is 40 pages */
ods rtf file="lr_params.rtf";
proc logistic data=claims; model outcome = age sex; run;
ods rtf close;
```

### Rule 4: `ODS GRAPHICS` is ON by default in SAS 9.4 — except in batch mode and on z/OS

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=odsug&docsetTarget=titlepage.htm

Beginning in SAS 9.4, ODS Graphics is enabled by default on all
platforms except z/OS, and procedures like LOGISTIC / MIXED / GLM
auto-emit diagnostic panels when the destination supports them.
In batch mode (`sas -batch`), however, the default flips to OFF —
so a LOGISTIC that renders plots interactively produces no plots
when scheduled as a batch job. Always set `ODS GRAPHICS ON;`
explicitly at the top of production code and `OFF;` after to
bound scope and avoid surprises from session-level state.

```sas
/* CORRECT - explicit on/off regardless of interactive vs batch */
ods graphics on / reset noborder imagename="lr_diag";
proc logistic data=claims plots=all;
  model outcome = age sex;
run;
ods graphics off;
```

```sas
/* WRONG - relies on default; no plots when run via sas -batch */
proc logistic data=claims plots=all;
  model outcome = age sex;
run;
```

### Rule 5: Destination options set at `ODS dest FILE=...` are global — nest `ODS dest OPTIONS(...)` between procs to change them per-PROC

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=odsug&docsetTarget=titlepage.htm

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

### Rule 6: `ODS _ALL_ CLOSE;` is the reset — use it at the top of a production script to guarantee clean state

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=odsug&docsetTarget=titlepage.htm

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

### Rule 7: Set `options replace=yes;` when `ODS OUTPUT Table=ds;` targets an existing dataset name

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=odsug&docsetTarget=titlepage.htm

The ODS OUTPUT statement documentation flags this explicitly: to
ensure the captured dataset is replaced on re-runs rather than
triggering an error, set `options replace=yes;` (which is the
default on most installs, but not all). When `REPLACE=NO` is
active — often the case in shops with tight data-loss policies —
re-running a script that writes `ODS OUTPUT PE=lr_pe;` errors on
the second run because `lr_pe` already exists.

```sas
/* CORRECT - replace is on; dataset overwrites cleanly on re-run */
options replace=yes;
ods output ParameterEstimates=lr_pe;
proc logistic data=claims; model outcome = age sex; run;
```

```sas
/* WRONG - in a REPLACE=NO session the second run errors out */
ods output ParameterEstimates=lr_pe;
proc logistic data=claims; model outcome = age sex; run;
/* rerun => "File WORK.LR_PE already exists and REPLACE=NO" */
```

### Rule 8: `ODS LISTING` is the default text destination — close it before opening RTF / PDF to avoid dumping a second copy to the `.lst`

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=odsug&docsetTarget=titlepage.htm

In interactive SAS and on most batch configurations, `ODS LISTING`
is open at session start. Opening an RTF or PDF does not close it;
your PROCs write to both. For a clean single-destination report,
`ods listing close;` before `ods rtf file=...;` and restore with
`ods listing;` after `ods rtf close;`. On SAS 9.4 with the default
session style, leaving LISTING open also means every QA script
emits a `.lst` file alongside the intended RTF.

```sas
/* CORRECT - LISTING closed for the RTF block, restored after */
ods listing close;
ods rtf file="report.rtf";
proc freq data=claims; tables dx_code; run;
ods rtf close;
ods listing;
```

```sas
/* WRONG - both LISTING and RTF receive output; duplicate .lst */
ods rtf file="report.rtf";
proc freq data=claims; tables dx_code; run;
ods rtf close;
```

## Canonical Idioms

### Idiom: Capture PROC LOGISTIC parameter estimates as a downstream-usable dataset

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=odsug&docsetTarget=titlepage.htm

Purpose: the most common ODS OUTPUT pattern in modeling pipelines —
pull the ParameterEstimates and FitStatistics tables out as SAS
datasets for merging into a results-summary table or forest-plot
input. `ods trace on` is how you discover the exact names; after
the first run, pin them in code.

```sas
ods output ParameterEstimates=lr_pe
           FitStatistics=lr_fit
           OddsRatios=lr_or;
proc logistic data=claims;
  class plan_type(ref='HMO') / param=ref;
  model outcome(event='1') = age sex plan_type;
run;
/* lr_pe has Variable, Estimate, StdErr, WaldChiSq, ProbChiSq */
```

### Idiom: Route a suite of PROCs to a single RTF report with `STYLE=`

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=odsug&docsetTarget=titlepage.htm

Purpose: the canonical claims-reporting pattern — several descriptive
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

### Idiom: Multi-sheet Excel with per-PROC sheet naming

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=odsug&docsetTarget=titlepage.htm

Purpose: the deliverable-to-a-clinician pattern — one xlsx with
Enrollment, Costs, Utilization tabs. Re-issue
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

### Idiom: Discover table names with `ODS TRACE ON;` before writing `ODS OUTPUT`

Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=odsug&docsetTarget=titlepage.htm

Purpose: the "what do I call this thing" discovery workflow. Run
the proc once with trace on, scan the log for output-object names,
then hardcode them into `ODS OUTPUT`. Essential for less-used
procs (NLMIXED, GLIMMIX) where the table inventory isn't memorized.

```sas
ods trace on / label;
proc glimmix data=claims;
  class plan_type;
  model paid_amt = age plan_type / dist=gamma link=log;
  random intercept / subject=site;
run;
ods trace off;
/* log prints: Name: ParameterEstimates, Label: "Solutions for Fixed Effects"
   Name: FitStatistics, Label: "Fit Statistics"
   Name: CovParms, Label: "Covariance Parameter Estimates" ... */
```

## Function / Statement Quick Ref

| Name | Syntax | Purpose | Common mistake | Doc URL |
|------|--------|---------|----------------|---------|
| `ODS RTF` | `ods rtf file='f.rtf' style=journal;` | Open RTF (Word) destination | Forgetting `ODS RTF CLOSE;` (Rule 1) | [ODS RTF Statement](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=odsug&docsetTarget=titlepage.htm) |
| `ODS EXCEL` | `ods excel file='f.xlsx' options(sheet_interval='proc');` | Open Excel (native xlsx) destination | No per-proc `sheet_name`; sheets named `Sheet1`... | [ODS EXCEL Statement](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=odsug&docsetTarget=titlepage.htm) |
| `ODS PDF` | `ods pdf file='f.pdf' style=journal;` | Open PDF destination | Omitting `STYLE=` → default style often has color backgrounds | [ODS PDF Statement](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=odsug&docsetTarget=titlepage.htm) |
| `ODS HTML` | `ods html file='f.html' path='out';` | Open HTML destination | Not setting `PATH=`; files scatter in working dir | [ODS HTML Statement](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=odsug&docsetTarget=titlepage.htm) |
| `ODS LISTING` | `ods listing close;` / `ods listing;` | The legacy text destination | Leaving it open duplicates output to `.lst` (Rule 8) | [ODS LISTING Statement](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=odsug&docsetTarget=titlepage.htm) |
| `ODS OUTPUT` | `ods output Table=ds Table2=ds2;` | Capture output objects as SAS datasets | Mis-typed table name → silent 0-row dataset (Rule 2) | [ODS OUTPUT Statement](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=odsug&docsetTarget=titlepage.htm) |
| `ODS TRACE ON` | `ods trace on / label;` | Log every output object's path + label | Leaving on → log floods with trace records | [ODS TRACE Statement](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=odsug&docsetTarget=titlepage.htm) |
| `ODS TRACE OFF` | `ods trace off;` | Stop tracing | Forgetting, then log fills with object records | [ODS TRACE Statement](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=odsug&docsetTarget=titlepage.htm) |
| `ODS SELECT` | `ods rtf select ParameterEstimates;` | Narrow a destination's output list | Scope ends at next PROC unless `PERSIST=PROC` | [ODS SELECT Statement](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=odsug&docsetTarget=titlepage.htm) |
| `ODS EXCLUDE` | `ods rtf exclude FitStatistics;` | Suppress one or more objects for a destination | Same scope caveat as SELECT | [ODS EXCLUDE Statement](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=odsug&docsetTarget=titlepage.htm) |
| `ODS GRAPHICS` | `ods graphics on / noborder imagename='x';` | Enable / configure template-based graphs | Relying on default — off in batch (Rule 4) | [ODS GRAPHICS Statement](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=odsug&docsetTarget=titlepage.htm) |
| `ODS _ALL_ CLOSE` | `ods _all_ close;` | Close every open destination | Calling mid-pipeline then forgetting to reopen one | [ODS _ALL_ CLOSE Statement](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=odsug&docsetTarget=titlepage.htm) |
| `dest OPTIONS(...)` | `ods excel options(sheet_name='x');` | Per-PROC destination option update | Setting only on `FILE=` and expecting per-sheet rename | [ODS EXCEL OPTIONS= Suboptions](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=odsug&docsetTarget=titlepage.htm) |
| `PROC TEMPLATE` | `proc template; define style s; ...; end; run;` | Define / modify style templates | Attempting to use a style not yet compiled in the libref | [PROC TEMPLATE Procedure](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=odsug&docsetTarget=titlepage.htm) |
| `options replace=yes` | `options replace=yes;` | Allow ODS OUTPUT target dataset to overwrite | Running under `REPLACE=NO` → second run errors (Rule 7) | [REPLACE= System Option](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=odsug&docsetTarget=titlepage.htm) |

## Silent Pitfalls

- **Forgotten `ODS dest CLOSE;`** — an open destination continues
  to receive output from every subsequent PROC in the session.
  Interactive sessions are especially prone to this. See Rule 1 and
  use `ods _all_ close;` at the top of production scripts (Rule 6).
  Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=odsug&docsetTarget=titlepage.htm

- **`ODS OUTPUT` table-name typo** — no error, no warning, just a
  silently empty dataset. Discover correct names via `ODS TRACE
  ON;`. See Rule 2.
  Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=odsug&docsetTarget=titlepage.htm

- **`ODS GRAPHICS` off in batch** — interactive `PROC LOGISTIC`
  produces diagnostic plots; the same code scheduled as `sas -batch`
  produces no plots because the default flips to OFF. Always
  explicit. See Rule 4.
  Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=odsug&docsetTarget=titlepage.htm

- **Excel auto-named sheets** — one `ODS EXCEL FILE=...` with no
  inter-proc `OPTIONS(SHEET_NAME=...)` gives Sheet1, Sheet2, etc.
  See Rule 5.
  Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=odsug&docsetTarget=titlepage.htm

- **Duplicate `.lst` alongside the RTF** — LISTING stays open when
  RTF opens; close it explicitly. See Rule 8.
  Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=odsug&docsetTarget=titlepage.htm

- **`REPLACE=NO` session re-run failure** — `ODS OUTPUT Table=ds;`
  errors on the second run if `ds` exists and `REPLACE=NO`. See
  Rule 7.
  Source: https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=odsug&docsetTarget=titlepage.htm

## Anti-patterns (STOP signs)

**STOP** when you see any of the following — the code runs but the
output is almost certainly not what the author meant:

- `ODS RTF FILE=...;` with no matching `ODS RTF CLOSE;` at the end
  of the script → see Rule 1. Subsequent procs append silently.
- `ODS OUTPUT ParamEstimates=...;` (misspelled) → see Rule 2.
  Silent zero-row capture.
- Relying on default `ODS GRAPHICS` state for batch / production
  code → see Rule 4. Set explicitly.
- `ODS EXCEL FILE=...;` followed by two PROCs with no inter-proc
  `SHEET_NAME=` → see Rule 5. Auto-named sheets.
- Omitting `ODS LISTING CLOSE;` before opening RTF / PDF when the
  goal is a single-destination report → see Rule 8.
- Long-running session that accumulates open destinations across
  interactive edits → fix with `ODS _ALL_ CLOSE;` (Rule 6).

## See Also

- [base-procs.md](base-procs.md) — `NOPRINT` on PROC MEANS /
  UNIVARIATE / FREQ when you only want the output dataset and no
  printed table; alternative to routing then excluding via ODS.
- [stat-procs.md](stat-procs.md) — common `ODS OUTPUT` targets
  for modeling procedures (ParameterEstimates, FitStatistics,
  OddsRatios, LSMeans, CovParms).
- [proc-sql.md](proc-sql.md) — `NOPRINT` on PROC SQL when only
  `INTO :mvar` or `CREATE TABLE AS` is wanted.
- [data-step.md](data-step.md) — `FILE` / `PUT` as the non-ODS
  text-output path; complementary to ODS for log-style output.
- [SAS Output Delivery System: User's Guide (9.4)](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=odsug&docsetTarget=titlepage.htm)
- [Base SAS Procedures Guide — ODS OUTPUT and ODS destinations (9.4)](https://documentation.sas.com/?cdcId=pgmsascdc&cdcVersion=9.4_3.5&docsetId=proc&docsetTarget=titlepage.htm)
