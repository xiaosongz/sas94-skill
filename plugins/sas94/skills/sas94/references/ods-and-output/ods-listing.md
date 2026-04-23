---
title: ODS LISTING text destination
loaded_when: '"ODS LISTING", "duplicate lst file", "lst alongside rtf", "close listing before rtf", "linesize", "ps=", or any task involving the legacy text destination.'
---

## Critical Rules

### Rule: `ODS LISTING` is the default text destination — close it before opening RTF / PDF to avoid dumping a second copy to the `.lst`

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

### Symmetric listing-close / reopen around a report block

Treat `ods listing close;` and `ods listing;` as the outer bracket
around any file-destination report. The paired form keeps interactive
sessions usable after the script finishes; pure batch scripts can
omit the reopen.

```sas
ods listing close;
ods rtf file="monthly.rtf" style=journal;
proc freq data=claims; tables dx_code; run;
proc means data=claims; var paid_amt; run;
ods rtf close;
ods listing;
```

### Text-only output with `options linesize=` and `ps=`

For log-style text output through the LISTING destination, page
geometry is controlled by `OPTIONS LINESIZE=` (column width) and
`OPTIONS PS=` (page size / lines-per-page). These do not affect
RTF / PDF / EXCEL output — they only apply to the text LISTING
destination and the SAS log.

```sas
options linesize=132 ps=60;
ods listing;
proc print data=claims(obs=20); run;
```

## Quick Ref

| Name | Syntax | Purpose | Common mistake |
|------|--------|---------|----------------|
| `ODS LISTING` | `ods listing close;` / `ods listing;` | The legacy text destination | Leaving it open duplicates output to `.lst` |
| `LINESIZE=` | `options linesize=132;` | LISTING column width | Setting it and expecting RTF / PDF to honor it |
| `PS=` | `options ps=60;` | LISTING page size (lines per page) | Same — does not affect non-LISTING destinations |

## Silent Pitfalls

- **Duplicate `.lst` alongside the RTF** — LISTING stays open when
  RTF opens; close it explicitly.
- **`LINESIZE=` / `PS=` applied to wrong destination** — these
  options only shape LISTING (and the log). An RTF author expecting
  `linesize=132` to widen a Word-table will be disappointed.
- **Forgotten reopen** — `ods listing close;` without a later
  `ods listing;` leaves an interactive session with no default text
  destination; subsequent PROCs render nothing visible in the
  Results window unless another destination is open.

## Anti-patterns

- Opening RTF / PDF for a "clean" single-destination report while
  leaving LISTING open. Every PROC dumps twice.
- Using `OPTIONS LINESIZE=` to try to format an RTF or EXCEL
  deliverable — it does not affect those destinations.

For the full RTF / PDF / EXCEL destination lifecycle see `ods-destinations.md`.
