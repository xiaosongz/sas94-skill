---
title: ODS GRAPHICS and style templates
loaded_when: '"ODS GRAPHICS", "imagename", "imagefmt", "proc template", "style template", "diagnostic plots missing", "batch mode plots", or any task involving PROC-emitted graphs or style customization.'
---

## Critical Rules

### Rule: `ODS GRAPHICS` is ON by default in SAS 9.4 — except in batch mode and on z/OS

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

## Canonical Idioms

### Bound ODS GRAPHICS around a PROC that emits diagnostic plots

`ODS GRAPHICS ON / RESET` clears any accumulated graphics options
from prior PROCs; `NOBORDER` removes the outer frame, and
`IMAGENAME=` sets the base filename for image files ODS writes
when the destination is HTML / PDF. The matching `OFF;` closes the
scope so later PROCs don't inherit the graphics state.

```sas
ods graphics on / reset noborder imagename="lr_diag" imagefmt=png;
proc logistic data=claims plots=(roc effect);
  model outcome(event='1') = age sex;
run;
ods graphics off;
```

### Define or modify a style template with PROC TEMPLATE

PROC TEMPLATE compiles a style into a template-store library
(default `SASUSER.TEMPLAT`) that later ODS destination calls can
reference by name. Attempting to use a style not yet compiled in
the libref is the common mistake — it fails silently back to the
default style on some destinations.

```sas
proc template;
  define style styles.claims_report;
    parent = styles.journal;
    style Body from Body /
      fontfamily = "Arial"
      fontsize   = 10pt;
  end;
run;

ods rtf file="report.rtf" style=claims_report;
proc freq data=claims; tables dx_code; run;
ods rtf close;
```

## Quick Ref

| Name | Syntax | Purpose | Common mistake |
|------|--------|---------|----------------|
| `ODS GRAPHICS` | `ods graphics on / noborder imagename='x';` | Enable / configure template-based graphs | Relying on default — off in batch |
| `IMAGENAME=` | `ods graphics on / imagename='lr_diag';` | Base filename for image files ODS writes | Leaving default → `SASGraph1`, `SASGraph2`... |
| `IMAGEFMT=` | `ods graphics on / imagefmt=png;` | Output image format (png / svg / jpg) | Mismatch with destination expectations |
| `PROC TEMPLATE` | `proc template; define style s; ...; end; run;` | Define / modify style templates | Using a style not yet compiled in the libref |

## Silent Pitfalls

- **`ODS GRAPHICS` off in batch** — interactive `PROC LOGISTIC`
  produces diagnostic plots; the same code scheduled as `sas -batch`
  produces no plots because the default flips to OFF. Always
  explicit.
- **Graphics state carry-over** — options set on one `ods graphics on`
  persist to the next PROC unless you `RESET` them; add `/ reset`
  when bounding around a single PROC.
- **Uncompiled style name** — `STYLE=claims_report` where the
  template was never compiled in `SASUSER.TEMPLAT` falls back to
  the default style without a clear error.

## Anti-patterns

- Relying on default `ODS GRAPHICS` state for batch / production
  code. Set `ods graphics on;` explicitly and close with `off;`.
- Leaving `IMAGENAME=` unset in a report where image files matter
  (HTML output directory fills with `SASGraph1.png`, `SASGraph2.png`).
- Referencing a style template before its `PROC TEMPLATE` compile
  step in the same script.

For destination-level `STYLE=` use see `ods-destinations.md`.
