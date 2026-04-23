---
title: Real-world SAS idioms (lexjansen / SUGI / SAS Global Forum) - index
loaded_when: Unknown or novel task, "how do SAS programmers do X", "Dorfman hash", "Lafler PROC SQL", "Whitlock macro quoting", or when no single topic-reference file clearly matches the request.
---

## Routing Table

Curated idioms harvested from practitioner-authored SUGI / NESUG / SESUG
/ WUSS / MWSUG / PhUSE conference papers. Complements the
SAS-docs-grounded topic files by attaching named-author history to
each idiom. Entry point when the task doesn't obviously map to a
single topic reference.

| Atom | One-line summary | Papers |
|------|------------------|--------|
| `hash-idioms.md` | Dorfman's DATA-step hash idioms: streaming reference lookup, `check()`+`add()` dedup, `find()`+`replace()` counter/aggregator, `multidata: 'Y'` + `find_next()` one-to-many join. Rule: small side in hash, large side streamed. | Dorfman, SUGI 30 (2005); NESUG 2007; SESUG 2015 |
| `sql-idioms.md` | Lafler's PROC SQL idioms: searched vs simple CASE with `ELSE` catch-all, `LEFT JOIN` + `COALESCE` for reference-table attach, the "duplicate matching column not automatically overlaid" trap. | Lafler, WUSS 2011; MWSUG 2015 |
| `macro-idioms.md` | Whitlock + Lepp macro-quoting: compile-time (`%STR` / `%NRSTR`) vs execution-time (`%BQUOTE` / `%NRBQUOTE` / `%SUPERQ`) split; `%NRSTR` + `%UNQUOTE` run-time object build; `%SUPERQ` for freeze-the-value reads. | Whitlock, NESUG 2009; Lepp, PhUSE 2019 |

## Topic Cluster Summary

**Hash cluster (Dorfman, 3 papers).** The 2005 SUGI 30 paper is the
tutorial of record — it introduces the `declare hash` / `definekey` /
`definedata` / `definedone` sequence, the iterator (`hiter`), and
the `if _N_ = 1 then do; ... end;` scoping pattern. The 2007 NESUG
"Hash Crash" paper extends this with aggregation idioms (the
summary-less summarization note) and the memory-footprint warning
that anchors the small-side-in-hash rule. The 2015 SESUG paper fills
in the `multidata: 'Y'` / `find_next()` mechanics that make
one-to-many joins possible without PROC SQL. The per-topic file
`../hash-tables/` cites all three and encodes their rules as
DATA-step-documentation-grounded syntax; this file documents them as
*named idioms* with the practitioner history attached.

**PROC SQL cluster (Lafler, 2 papers).** The WUSS 2011 paper is
narrowly about CASE expressions — simple vs searched, the `ELSE`
catch-all, and the claim that searched CASE is the primary form
practitioners reach for. The MWSUG 2015 paper is a guided tour of
the match-join matrix with Venn-diagram illustrations, and is the
source for the "duplicate matching column is not automatically
overlaid" rule that anchors `../proc-sql/joins.md`. Together they
cover the two most common claims-analytics uses of PROC SQL:
row-level conditional columns and reference-table joins. Note: a
third Lafler paper ("Best Tips and Techniques Using PROC SQL", SGF
2011 paper 101) was in our scraper seeds but the cached file turned
out to contain a different paper (Gamishev on email management) — it
is not cited here.

**Macro-quoting cluster (Whitlock + Lepp, 2 papers).** Whitlock's
NESUG 2009 paper is the long-form explanation of why macro quoting
even exists — "the fact that [the] same word or combination of
symbols can have meanings in both SAS and macro that is the root
cause for requiring quoting" — and walks through `%STR`, `%NRSTR`,
`%QUOTE`, `%BQUOTE`, `%NRQUOTE`, `%NRBQUOTE`, `%SUPERQ`, and
`%UNQUOTE` with worked examples. Lepp's PhUSE 2019 paper is the
complementary short-form: it diagrams the Input Stack / Word Scanner
/ Macro Processor interaction and shows how the compile-time /
execution-time split falls out of the processing order. The
Whitlock paper is the "why"; the Lepp paper is the "when."

Cross-refs: `../hash-tables/`, `../proc-sql/`, `../macros/`,
`../data-step/merge.md`, `../data-step/sql-vs-merge.md`.
