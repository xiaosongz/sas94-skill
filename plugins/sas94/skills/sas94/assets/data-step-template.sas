/*****************************************************************************
 * File:     data-step-template.sas
 * Purpose:  Boilerplate DATA step program skeleton for new SAS 9.4 work.
 * Version:  0.0.1
 * License:  MIT -- see LICENSE at repo root.
 *
 * This file is a template. Add your DATA step logic below.
 * See references/data-step.md for MERGE / BY / retain / array idioms.
 *****************************************************************************/

/* -------------------------------------------------------------------------- */
/* 1. Library setup                                                           */
/* -------------------------------------------------------------------------- */

/* TODO: replace placeholder path with your project work area */
libname mylib "/tmp/mylib";

/* -------------------------------------------------------------------------- */
/* 2. DATA step -- canonical patterns                                         */
/*    - set from a source                                                     */
/*    - merge with by + first./last. handling                                 */
/*    - retain for running state                                              */
/*    - array for repeated-variable operations                                */
/*    - call missing for PDV init                                             */
/*    - keep / drop / rename at end                                           */
/* -------------------------------------------------------------------------- */

data mylib.analysis_out(keep=patient_id visit_dt cost_total cost_avg
                             cost_month1-cost_month3 first_visit_flag);

  /* TODO: replace placeholder source datasets with real inputs */
  merge mylib.claims(in=a rename=(cost=cost_claim))
        mylib.enrollment(in=b rename=(cost=cost_enroll));
  by patient_id visit_dt;

  /* Keep only patients present in both sources */
  if a and b;

  /* retain for running state within by-group -- reset on first.patient_id */
  retain cost_running 0 visit_count 0;

  if first.patient_id then do;
    /* call missing initializes multiple PDV vars in one call */
    call missing(cost_running, visit_count, cost_month1, cost_month2,
                 cost_month3);
    first_visit_flag = 1;
  end;
  else first_visit_flag = 0;

  /* Running state accumulates across rows within by-group */
  cost_running + coalesce(cost_claim, cost_enroll, 0);
  visit_count + 1;

  /* array for repeated-variable operations across monthly buckets */
  array cost_m{3} cost_month1-cost_month3;
  do i = 1 to dim(cost_m);
    if month(visit_dt) = i then cost_m{i} = coalesce(cost_claim, 0);
  end;

  /* Emit one row per patient on last.patient_id -- summary row */
  if last.patient_id then do;
    cost_total = cost_running;
    if visit_count > 0 then cost_avg = cost_total / visit_count;
    else cost_avg = .;
    output;
  end;

  drop i cost_claim cost_enroll cost_running visit_count;
run;

/* -------------------------------------------------------------------------- */
/* 3. Verification                                                            */
/* -------------------------------------------------------------------------- */

proc means data=mylib.analysis_out n mean min max;
  var cost_total cost_avg;
run;

proc print data=mylib.analysis_out(obs=10);
  title "analysis_out -- first 10 rows";
run;
title;
