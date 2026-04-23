---
title: ODS and output reference index
loaded_when: '"ODS", "output delivery", "route proc output", "capture proc table as dataset", or any ODS-related task before a specific atom is known.'
---

## Routing table

Load the atom whose triggers best match the task. Keep this index under 50 lines.

| Atom | One-line summary | Load when |
|------|------------------|-----------|
| `ods-output-capture.md` | `ODS OUTPUT Table=ds;` pattern, `ODS TRACE ON;` discovery, silent-empty failure on mis-typed table name, `options replace=yes;` caveat. | Capturing a PROC's named output object as a SAS dataset (ParameterEstimates, FitStatistics, etc.); diagnosing a 0-row captured dataset; discovering output-object names. |
| `ods-destinations.md` | RTF / PDF / EXCEL / HTML destinations, `style=` option, `options(...)` per-PROC suboptions, open/close lifecycle, `ods _all_ close`, duplicate-append pitfalls. | Routing PROCs to a Word / PDF / Excel / HTML report; multi-sheet Excel; multi-PROC RTF; fixing forgotten-close or duplicate-append bugs. |
| `ods-graphics.md` | `ODS GRAPHICS ON/OFF`, `imagename=`, batch-vs-interactive default flip, PROC TEMPLATE style definition. | Producing diagnostic plots from LOGISTIC / MIXED / GLM; debugging missing plots in batch; customizing style templates. |
| `ods-select-exclude.md` | `ODS dest SELECT` / `ODS dest EXCLUDE` to filter which PROC output objects render on a destination; default SELECT ALL (except OUTPUT = EXCLUDE ALL); scope resets per-PROC. | Narrowing an RTF / PDF to a single table; suppressing FitStatistics from a destination; filtering output without NOPRINT. |
| `ods-listing.md` | `ODS LISTING` text destination, close-before-RTF discipline, duplicate `.lst` pitfall. | Suppressing `.lst` duplicates; opening / closing the legacy text destination around a report block. |

## Quick triage

- "Dataset is empty after ODS OUTPUT" → `ods-output-capture.md` (table-name typo).
- "RTF file won't open in Word" → `ods-destinations.md` (forgotten close).
- "No plots when I run this in batch" → `ods-graphics.md` (default flips to OFF).
- "Excel tabs named Sheet1, Sheet2" → `ods-destinations.md` (per-PROC OPTIONS).
- "Extra .lst file alongside my RTF" → `ods-listing.md` (LISTING still open).
- "My RTF has 40 pages but I only wanted one table" → `ods-select-exclude.md`.

## Cross-topic references

- `../base-procs/<proc>.md` — `NOPRINT` option on MEANS / UNIVARIATE / FREQ when only an OUTPUT dataset is wanted (alternative to routing via ODS).
- `../stat-procs/<proc>.md` — common `ODS OUTPUT` targets for modeling PROCs (ParameterEstimates, FitStatistics, OddsRatios, LSMeans, CovParms).
- `../data-step/file-hygiene.md` — `FILE` / `PUT` as the non-ODS text-output path.
- PROC SQL `NOPRINT` (separate topic) — when only `INTO :mvar` or `CREATE TABLE AS` is wanted.
