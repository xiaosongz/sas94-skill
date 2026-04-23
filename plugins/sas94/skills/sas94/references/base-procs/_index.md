---
title: Base SAS procedures — routing index
loaded_when: '"PROC FREQ", "PROC MEANS", "PROC UNIVARIATE", "PROC SORT", "PROC TRANSPOSE", "PROC REPORT", "PROC PRINT", "PROC CONTENTS", "PROC DATASETS", "PROC IMPORT", "PROC EXPORT", "PROC COMPARE", "NODUPKEY", "OUTPUT OUT=", "DBMS=", "GETNAMES=", schema inspection, library cleanup, CSV / Excel IO, or dataset-equality testing.'
---

## Routing decision tree

Pick the atom that matches the user's question. Every atom lives in
this directory (`references/base-procs/`); load only what's needed.

- Counts / cross-tabs / frequency tables → `proc-freq.md`
  (default drops missing from denominator; `OUT=` idiom)
- Descriptive stats (`sum`, `mean`, `n`) rolled up by CLASS var →
  `proc-means.md` (`NOPRINT`, `OUTPUT OUT=` with named stats)
- Quantiles / extended descriptives / distribution moments →
  `proc-univariate.md` (`NOPRINT` extraction pattern)
- Order rows / dedup by key / dedup full row → `proc-sort.md`
  (`OUT=` to preserve input, `NODUPKEY` vs `NODUPRECS`, `DUPOUT=`)
- Long ↔ wide reshape → `proc-transpose.md`
  (always spell out `VAR` — default drops character columns)
- Grouped/summarized formatted report → `proc-report.md`
  (`DEFINE ... / GROUP` vs `DISPLAY` vs `ANALYSIS` vs `ORDER`)
- Plain listing / quick dataset dump → `proc-print.md`
  (`NOOBS`, `VAR` ordering, `LABEL`)
- Schema inspection / library metadata edits / selective delete →
  `schema-utils.md` (`PROC CONTENTS`, `PROC DATASETS`; `KILL` trap)
- CSV / Excel read or write → `file-io.md`
  (`PROC IMPORT` / `EXPORT`; `GUESSINGROWS=MAX`, explicit `DBMS=`)
- Dataset equality / diff two datasets → `proc-compare.md`
  (default `METHOD=EXACT`; `CRITERION=` semantics)

## Cross-topic pointers

- SQL alternatives (`SELECT DISTINCT`, `GROUP BY`) — see the PROC SQL
  reference.
- Statistical modeling (`LOGISTIC`, `GLM`, `MIXED`, `GENMOD`,
  `LIFETEST`, `PHREG`, `SURVEYMEANS`) — see `../stat-procs/<proc>.md`.
- Routing output to Excel/RTF/PDF — see the ODS reference.
- Value labels used by FREQ/MEANS/REPORT for display — see the
  formats/informats reference.
- DATA-step dedup + `first.`/`last.` as an alternative to `PROC SORT
  NODUPKEY` — see `../data-step/merge.md` and `../data-step/retain-pdv.md`.
