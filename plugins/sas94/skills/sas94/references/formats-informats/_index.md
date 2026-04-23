---
title: Formats and informats — routing index
loaded_when: '"format", "informat", "PROC FORMAT", "VALUE", "INVALUE", "PICTURE", "CNTLIN", "put(", "input(", "mmddyy", "yymmdd", "datetime", "anydtdte", "DATESTYLE", or any user-defined format / informat / date parsing task.'
---

## Routing Table

Formats and informats are SAS's bidirectional bridge: a **format**
converts a stored value to a display string (`put(x, dollar12.2)` →
`'$1,234.56'`); an **informat** converts an input string to a stored
value (`input('01/02/2020', mmddyy10.)` → SAS date `21916`). Every
format reference ends in a period; every `VALUE` / `INVALUE` /
`PICTURE` definition does not.

Split into four atoms plus this index — load only what the current
task needs.

| Atom | Load when | Covers |
|------|-----------|--------|
| [put-vs-input.md](put-vs-input.md) | Any `put()` / `input()` call; direction confusion; run-time format names | Direction rule, trailing-dot requirement, `putn` / `putc` / `inputn` / `inputc` run-time variants, FORMAT vs INFORMAT statement split |
| [proc-format.md](proc-format.md) | Building a user format; `VALUE` / `INVALUE` / `PICTURE`; `CNTLIN=` / `CNTLOUT=` | PROC FORMAT definition statements, control-dataset round-trip, `OTHER=` catch-all, PICTURE digit selectors |
| [date-formats.md](date-formats.md) | Reading or writing date / datetime columns; messy vendor date strings | `mmddyy10.`, `yymmdd10.`, `date9.`, `datetime20.`, `anydtdte.` + `DATESTYLE=`, informat vs format pairing |
| [numeric-formats.md](numeric-formats.md) | Dollar / comma / best formats; width-truncation asterisks; coercing character-numeric | `best.`, `dollar.`, `comma.`, `w.d` precision, too-narrow-width asterisks, `input(str, best.)` coercion |

## Cross-topic references

- `../data-step/file-hygiene.md` — `FORMAT` / `INFORMAT` / `LENGTH` /
  `ATTRIB` statements and how attached attributes propagate.
- `../base-procs/proc-freq.md`, `../base-procs/proc-report.md` — procs
  that honor attached formats for display grouping.
- Date-arithmetic functions (`INTCK`, `INTNX`, `MDY`, `DATEPART`) are
  in the functions reference (split in parallel).
