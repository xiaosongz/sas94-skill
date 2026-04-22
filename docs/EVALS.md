# Evaluation architecture

The skill ships with a minimal regression-baseline eval in `evals/`. This
document covers the architectural stance; the how-to-run lives in
[`evals/README.md`](../evals/README.md).

## What passing means

The eval loads `SKILL.md` and every `references/*.md` as a cached system
message, sends three prompts to `claude-opus-4-7`, and checks each response
for a short list of regex patterns plus a `min_word_count` floor.

A passing run means: **loaded into Claude, the skill content still produced
SAS code that carried the structural markers the rules and idioms demand.**

Nothing more. Specifically, a passing run does **not** tell you:

- Whether the generated SAS compiles
- Whether the generated SAS gives correct results
- Whether rule edits are improvements vs. regressions in quality

Pattern matching is a structural check. A rule could produce
syntactically-plausible-but-semantically-wrong code — wrong `event=` value,
wrong `ODS OUTPUT` dataset name, wrong `CLASS` variable handling — and still
pass the eval. We accept that. Semantic correctness would need a live SAS
runtime, which is out of scope for a public, MIT-licensed skill.

## The three prompts

Each of the three prompts probes a specific differentiator the skill claims
over a generic LLM writing SAS. The claims:

1. **`01_macro_libref`** — claim: the skill enforces `sasjs/core` macro
   conventions from `references/macros.md` and the `idioms-from-lexjansen.md`
   file. A passing response carries `/*/STORE SOURCE*/` in the signature (or
   an equivalent `sasjs/core` registration form), a named `%mend <name>;`
   instead of a bare `%mend;`, and at least one `%local` declaration. A
   generic LLM typically produces `%macro name; ... %mend;` without those
   markers.

2. **`02_proc_append_debug`** — claim: the skill surfaces the PROC APPEND
   silent-failure mode documented in `references/base-procs.md` —
   specifically that `FORCE` only drops the WARNING when the DATA set has
   extra columns BASE lacks, and does nothing for the reverse case (BASE has
   a column DATA is missing, which silently appends missing values into
   BASE). Passing responses mention `FORCE` semantics, recommend reshaping
   DATA via `keep=` or `rename=` on input, and flag the silent-missing-column
   case. A generic LLM typically stops at "add `FORCE`" and misses the silent
   case.

3. **`03_logistic_event`** — claim: the skill enforces the event-pinning
   rule from `references/stat-procs.md` (Rule 2 / `LOGISTIC models
   P(Y = lowest ordinal value) by default`) and the ODS OUTPUT pattern from
   `references/ods-and-output.md`. Passing responses use `descending` or an
   explicit `event=` quoted level, declare `sex` via `CLASS`, and capture
   odds ratios via `ODS OUTPUT OddsRatios=...;`. A generic LLM frequently
   omits the event pin — producing a model of `P(died_30d = 0)` and
   flipping the direction of every odds ratio.

If any of these fails, the skill is no longer delivering the guardrail it
claims to deliver. That is the regression worth catching.

## Cadence

Run the eval locally before tagging a new version. It takes a minute and
costs roughly $0.50 on a cold cache, ~$0.10 warm. Log the run in the release
notes.

CI integration is deferred. Running this on every push would burn ~$15/month
for a low-traffic repo and much more for an active one; it also requires an
org-level API key in a public-repo Actions runner, which is not obviously
safe. Revisit in v0.0.2 with a `workflow_dispatch`-only trigger so the
maintainer can run it from the Actions tab without it firing on every PR.

## Known limitations

- **No semantic check.** Patterns match structure, not meaning. See above.
- **Model-sensitive.** Prompts are tuned for Opus 4.7. Swapping to a
  different model may require pattern re-tuning; the expected patterns have
  been kept conservative (structural SAS tokens, not prose phrases) to reduce
  that drift.
- **Three prompts is a small sample.** A rule can regress without showing up
  here. Expanding coverage is cheap — add a prompt under `evals/prompts/`
  per `evals/README.md`'s instructions — but every added prompt is another
  ~$0.02 per eval run.
- **Cache-dependent cost.** The ~$0.10 warm-cache number assumes the skill
  content hasn't changed between runs. If you edited a reference file, the
  cache is invalidated and you pay cold-start pricing again.
