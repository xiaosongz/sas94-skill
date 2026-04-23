---
title: PROC IMPORT + PROC EXPORT — CSV / Excel IO
loaded_when: '"PROC IMPORT", "PROC EXPORT", "DBMS=", "GETNAMES=", "GUESSINGROWS=", "CSV", "XLSX", "Excel", "SHEET=", "DLM=", "silent truncation", or "type coercion on import".'
---

## Critical Rules

### Rule 10 (IMPORT half): `PROC IMPORT` guesses types from a tiny sample — pin `DBMS=`, `GETNAMES=`, `GUESSINGROWS=MAX`

`PROC IMPORT` infers column types by scanning a small number of input
rows. For `DBMS=CSV` / `DLM` / `TAB` the default is `GUESSINGROWS=1`
(row 1 alone sets the column's type and length); the XLSX libname
engine scans more rows, but still not all. If row 5000 contains a
wider string than row 1, the step silently truncates; if a numeric-
looking row 1 is followed by a character-bearing row 500, the column
coerces. Always specify `DBMS=` (never rely on filename guessing),
set `GETNAMES=YES` explicitly, and raise `GUESSINGROWS=MAX` for
heterogeneous data. `PROC EXPORT` has the inverse problem — no
formatting by default; use `DBMS=XLSX` for typed round-tripping,
`DBMS=CSV` for plain text.

```sas
/* CORRECT - explicit DBMS / GETNAMES / GUESSINGROWS */
proc import datafile='/data/claims_2024.csv'
            out=work.claims_raw
            dbms=csv
            replace;
  getnames=yes;
  guessingrows=max;
run;

/* CORRECT - typed Excel export */
proc export data=work.claims_summary
            outfile='/out/summary.xlsx'
            dbms=xlsx
            replace;
  sheet='ClaimsSummary';
run;
```

```sas
/* WRONG - no DBMS, no GETNAMES, default GUESSINGROWS=1 for CSV; silent truncation */
proc import datafile='/data/claims_2024.csv' out=work.claims_raw replace;
run;
/* - column types / lengths inferred from row 1 alone (CSV default
     GUESSINGROWS=1);
   - a 120-char NDC code string in row 5000 truncates to the row-1 length;
   - GETNAMES defaults to YES for CSV / DLM / TAB, but not every DBMS.      */
```

## Quick Ref

| Option / statement | Purpose | Common mistake |
|--------------------|---------|----------------|
| `dbms=csv` / `xlsx` / `dlm` / `tab` | Specify file format | Relying on filename guessing |
| `getnames=yes` | Row 1 → column names | Off for XLSX by default in some versions |
| `guessingrows=max` | Scan every row for type / length | Default 1 for CSV → truncation |
| `replace` | Overwrite existing output | Omitting → step fails if file exists |
| `sheet='Name'` (XLSX) | Choose worksheet for EXPORT | Omitting → writes to default sheet name |
| `dbms=xlsx` (EXPORT) | Typed Excel round-trip | `dbms=csv` loses formatting |

## Anti-patterns (STOP signs)

- `proc import datafile=...;` with no `DBMS=` / no `GUESSINGROWS=MAX`
  on wide-row CSV → silent truncation / type coercion.

Cross-ref: for dataset-equality testing after round-trip see
`proc-compare.md`; for value-label / format preservation on export see
the formats/informats reference.
