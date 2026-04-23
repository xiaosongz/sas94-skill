/*****************************************************************************
 * File:     analysis-template.sas
 * Purpose:  End-to-end study-program scaffold for a new SAS 9.4 analysis.
 * Version:  0.0.1
 * License:  MIT -- see LICENSE at repo root.
 *
 * This file is a template. Add your analysis logic below.
 * For SAS 9.4 style/idiom rules, see the skill's topic atoms under
 * references/ (one directory per topic); SKILL.md is the authoritative
 * routing table that maps your task to the right atom(s).
 *****************************************************************************/

/* ========================================================================== */
/* Study header                                                               */
/* ========================================================================== */
/* Study name:     TODO -- replace with study short name                      */
/* Version:        0.0.1                                                      */
/* Date:           TODO -- YYYY-MM-DD                                         */
/* Analyst:        TODO -- name / ORCID                                       */
/* Source data:    TODO -- dataset provenance, version, extract date          */
/* Output target:  TODO -- report destination, delivery channel               */
/* ========================================================================== */

/* -------------------------------------------------------------------------- */
/* 0. Options and environment                                                 */
/* -------------------------------------------------------------------------- */

options nomlogic nomprint nosource2 validvarname=v7 nofmterr;

/* TODO: replace placeholder paths with your real input/output locations */
libname indata  "/tmp/indata"  access=readonly;
libname outdata "/tmp/outdata";

%let study_id    = TEMPLATE_STUDY;
%let run_dt      = %sysfunc(today(), yymmdd10.);
%let report_rtf  = /tmp/outdata/&study_id._&run_dt..rtf;

/* ========================================================================== */
/* 1. Data preparation                                                        */
/* ========================================================================== */

data work.claims_prep;
  set indata.claims;
  /* TODO: replace placeholder derivations with study-specific cleaning */
  where service_dt between '01JAN2023'd and '31DEC2023'd
    and not missing(patient_id);

  /* Cast cost to non-negative; flag outliers */
  if missing(cost) or cost < 0 then cost = 0;
  high_cost_flag = (cost > 10000);

  /* Derive service year for cohort slicing */
  service_yr = year(service_dt);

  keep patient_id service_dt service_yr cost high_cost_flag diagnosis_code;
run;

data work.enroll_prep;
  set indata.enrollment;
  /* TODO: replace placeholder cleaning with study-specific rules */
  where not missing(patient_id)
    and enroll_start le enroll_end;
  keep patient_id plan_id enroll_start enroll_end;
run;

/* ========================================================================== */
/* 2. Cohort definition                                                       */
/* ========================================================================== */

proc sql;
  create table work.cohort as
    select
      c.patient_id,
      e.plan_id,
      sum(c.cost)                 as cost_total label='Total cost',
      count(distinct c.service_dt) as visit_n   label='Distinct visit days',
      min(c.service_dt)           as first_dt   format=date9.,
      max(c.service_dt)           as last_dt    format=date9.
    from work.claims_prep  as c
      inner join work.enroll_prep as e
        on c.patient_id = e.patient_id
       and c.service_dt between e.enroll_start and e.enroll_end
    /* TODO: refine inclusion criteria for your study */
    group by c.patient_id, e.plan_id
    having calculated visit_n >= 1
    ;
quit;

/* ========================================================================== */
/* 3. Descriptive statistics                                                  */
/* ========================================================================== */

proc means data=work.cohort n mean std median min p25 p75 max maxdec=2;
  var cost_total visit_n;
  output out=outdata.cohort_means(drop=_type_ _freq_)
    n=n mean=mean std=std median=median;
run;

proc freq data=work.cohort;
  tables plan_id / missing nocum;
  /* TODO: add cross-tabs as needed, e.g. plan_id * age_band */
run;

proc freq data=work.claims_prep;
  tables service_yr * high_cost_flag / nocol nopercent;
run;

/* ========================================================================== */
/* 4. Analysis                                                                */
/* ========================================================================== */

/* TODO: replace this placeholder PROC with your specific analytic procedure
   (e.g. proc logistic / proc genmod / proc lifetest / proc glm).           */
proc univariate data=work.cohort noprint;
  var cost_total;
  output out=outdata.cost_quantiles
    pctlpts=10 25 50 75 90
    pctlpre=p;
run;

/* ========================================================================== */
/* 5. Output / reporting                                                      */
/* ========================================================================== */

ods _all_ close;
ods rtf file="&report_rtf" style=journal bodytitle;

title1 "&study_id -- analysis report";
title2 "Run date: &run_dt";

proc print data=outdata.cohort_means label noobs;
  title3 "Cohort descriptive statistics";
run;

proc print data=outdata.cost_quantiles label noobs;
  title3 "Cost-total quantiles";
run;

title;
footnote;

ods rtf close;
ods _all_ close;
ods listing;

%put NOTE- report written to &report_rtf;
