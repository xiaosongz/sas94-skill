/**
  @file macro-template.sas
  @brief Boilerplate %macro / %mend skeleton for new SAS 9.4 macro work.
  @details
    This file is a template. Add your macro logic below. Always use a
    parenthesized signature (sasjs/lint hasMacroParentheses). See
    references/macros.md for scope and quoting idioms.

    Version:  0.0.1
    License:  MIT -- see LICENSE at repo root.

  @param [in] libds     Positional-required. Two-level dataset name
                        (`library.member`) that the macro operates on.
  @param [in] outds=    Keyword-optional. Output dataset name. Defaults to
                        `work._mytmpl_out`.
  @param [in] iftrue=   Keyword-optional. Predicate that gates execution;
                        macro %returns early when it evaluates false.
                        Defaults to %str(1=1).

  @version 9.4
  @author  xiaosongz

  @cond
**/

%macro my_template(libds, outds=work._mytmpl_out, iftrue=%str(1=1)
)/des='skeleton macro with param guards and %local discipline' /*STORE SOURCE*/;

  /* %local discipline -- declare every non-parameter symbol upfront so the
     macro does not leak into the caller's scope. */
  %local nobs rc msg;

  /* Guarded execution -- caller can suppress side effects with iftrue= */
  %if not(%eval(%unquote(&iftrue))) %then %return;

  /* Error handling: validate positional-required input exists */
  %if %length(&libds) = 0 %then %do;
    %put ERROR: [&sysmacroname] libds is required but was empty.;
    %return;
  %end;

  %if %sysfunc(exist(&libds)) ne 1 %then %do;
    %put ERROR: [&sysmacroname] input dataset &libds does not exist.;
    %return;
  %end;

  /* Representative body: observation-count via %sysfunc + simple derivation
     TODO: replace with your real macro logic */
  %let rc = %sysfunc(open(&libds));
  %if &rc = 0 %then %do;
    %put ERROR: [&sysmacroname] could not open &libds (%sysfunc(sysmsg())).;
    %return;
  %end;
  %let nobs = %sysfunc(attrn(&rc, nlobs));
  %let rc = %sysfunc(close(&rc));

  %let msg = &sysmacroname processed &libds with &nobs obs -> &outds;
  %put NOTE- &msg;

  /* TODO: replace this placeholder body with your actual transformation */
  data &outds;
    set &libds;
    /* TODO: derived columns go here */
  run;

%mend my_template;

/* ------------------------------------------------------------------------- */
/* Example call site (commented-out -- uncomment and edit to use)            */
/* ------------------------------------------------------------------------- */
/*
libname mylib "/tmp/mylib";
%my_template(mylib.claims, outds=work.claims_out)
*/

/** @endcond **/
