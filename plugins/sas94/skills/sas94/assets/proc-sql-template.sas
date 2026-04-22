/*****************************************************************************
 * File:     proc-sql-template.sas
 * Purpose:  Boilerplate PROC SQL program skeleton for new SAS 9.4 work.
 * Version:  0.0.1
 * License:  MIT -- see LICENSE at repo root.
 *
 * This file is a template. Add your PROC SQL logic below.
 * See references/proc-sql.md for join, dedup, and INTO :macvar idioms.
 *****************************************************************************/

/* -------------------------------------------------------------------------- */
/* 1. Library setup                                                           */
/* -------------------------------------------------------------------------- */

/* TODO: replace placeholder path with your project work area */
libname mylib "/tmp/mylib";

/* -------------------------------------------------------------------------- */
/* 2. PROC SQL -- canonical patterns                                          */
/*    - explicit inner/left join (never implicit FROM a, b)                   */
/*    - coalesce for NULL handling across join sides                          */
/*    - group by + aggregate                                                  */
/*    - having filter                                                         */
/*    - into :macvar_list separated by ' ' for macro-driven loops             */
/* -------------------------------------------------------------------------- */

proc sql;

  /* TODO: replace placeholder source tables with real inputs */
  create table mylib.patient_costs as
    select
      c.patient_id           label='Patient ID',
      e.plan_id              label='Plan ID',
      count(distinct c.claim_id)                 as claim_n  label='Claims',
      sum(coalesce(c.cost, 0))                   as cost_sum label='Total cost',
      avg(coalesce(c.cost, 0))                   as cost_avg label='Mean cost',
      min(c.service_dt)                          as first_dt format=date9.,
      max(c.service_dt)                          as last_dt  format=date9.
    from mylib.claims     as c
      inner join mylib.enrollment as e
        on c.patient_id = e.patient_id
       and c.service_dt between e.enroll_start and e.enroll_end
    /* TODO: replace placeholder filter with real cohort criteria */
    where c.cost is not missing
      and c.service_dt between '01JAN2023'd and '31DEC2023'd
    group by c.patient_id, e.plan_id
    having calculated claim_n >= 2
    order by cost_sum desc
    ;

  /* into :macvar list pattern -- feed downstream %do loops */
  select distinct plan_id
    into :plan_list separated by ' '
    from mylib.patient_costs
    ;

  /* Scalar-count macro var for log diagnostics */
  select count(*)
    into :n_patients trimmed
    from mylib.patient_costs
    ;

quit;

%put NOTE- plan_list  = &plan_list;
%put NOTE- n_patients = &n_patients;

/* -------------------------------------------------------------------------- */
/* 3. Verification                                                            */
/* -------------------------------------------------------------------------- */

proc print data=mylib.patient_costs(obs=10);
  title "patient_costs -- first 10 rows";
run;
title;
