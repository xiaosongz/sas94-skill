# Evaluation architecture

The skill ships with a minimal regression-baseline eval in `evals/`. This
document covers the architectural stance; the how-to-run lives in
[`evals/README.md`](../evals/README.md).

## Why it's a manual harness

The skill is activated inside a Claude Code session via on-demand routing
per `SKILL.md`'s Reference Routing table — not via direct Anthropic-API
calls that bulk-load every reference file. Automating the eval through the
API would simulate a different routing path than what ships. So the harness
is intentionally manual: the maintainer runs each prompt inside a real
Claude Code session with the skill installed, pastes Claude's reply into a
transcript file, and a stdlib-only Python runner pattern-checks the
transcripts.

No API key, no `anthropic` SDK dependency, no cost per run. The cost is
maintainer-time: ~5 minutes per release to run three prompts and paste
three transcripts.

## What passing means

A passing run means: **loaded into a Claude Code session, the skill still
produced SAS code that carried the structural markers the rules and idioms
demand.**

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

Run the eval locally before tagging a new version. Each prompt takes ~90
seconds of maintainer time — open a fresh Claude Code session, paste the
prompt, save the reply, move on. Log the run in the release notes.

CI integration is not planned. Running the prompts automatically would
require either (a) an automated Claude Code session invocation (not a
stable CLI surface as of the 2.x docs), or (b) direct Anthropic API calls
that simulate rather than test the shipped routing path. Neither matches
the "test the skill as shipped" objective.

## Known limitations

- **No semantic check.** Patterns match structure, not meaning.
- **Manual workflow.** Someone has to run three Claude Code prompts and save
  transcripts per release. The cost is five minutes, not automatable
  without changing what's being tested.
- **Three prompts is a small sample.** A rule can regress without showing up
  here. Expanding coverage is cheap — add a prompt under `evals/prompts/`
  per `evals/README.md`'s instructions — but every added prompt adds
  ~90 seconds of manual-run time per release.
- **Model-sensitive.** Prompts are tuned against whatever model Claude Code
  is currently defaulting to. Swapping models may require pattern
  re-tuning; the expected patterns have been kept conservative (structural
  SAS tokens, not prose phrases) to reduce that drift.
