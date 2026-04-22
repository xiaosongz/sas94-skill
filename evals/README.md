# Evaluation harness

Regression-baseline for `sas94-skill`. Answers one question: does the skill,
loaded into a Claude Code session with its on-demand reference-file routing,
still produce SAS code that carries the structural markers the rules and
idioms in `references/*.md` demand?

Three prompts. Regex pattern-matching against transcripts. No semantic SAS
verification. Job: catch a regression where a reference-file edit quietly
removes a guardrail — not grade correctness.

## Why it's not automated

The skill is activated inside Claude Code via on-demand routing per
`SKILL.md`'s Reference Routing table — not via direct Anthropic-API calls
that bulk-load every reference file. Automating the eval through the API
would simulate a different routing path than what ships. So the harness is
intentionally manual: the user runs each prompt inside a real Claude Code
session with the skill installed, pastes the reply into a transcript file,
and the runner pattern-checks the transcript.

No API key, no `anthropic` SDK dependency, no cost per run. The runner is
stdlib Python only.

## How to run

1. Install the skill per `README.md` § Installation.
2. For each file under `evals/prompts/*.md`:
   a. Open a fresh Claude Code session.
   b. Paste the prompt body (the text after the second `---`).
   c. Save Claude's reply to `evals/transcripts/<prompt-id>.txt`. The
      `<prompt-id>` must match the frontmatter `id:` (e.g.
      `01_macro_libref.txt`).
3. From the repo root, run:

   ```bash
   uv --directory pipeline run python ../evals/run_evals.py
   ```

Exit codes:

- `0` — every transcript matched every pattern and cleared the
  `min_word_count` floor.
- `1` — at least one transcript failed a check.
- `2` — one or more transcripts are missing for declared prompts.

The `evals/transcripts/` directory is gitignored — transcripts are
ephemeral per-run artifacts, not content that belongs in version control.

## What the prompts test

Each prompt targets one of the skill's claimed differentiators vs. a generic
LLM writing SAS:

| Prompt                     | Differentiator                                                          |
|----------------------------|-------------------------------------------------------------------------|
| `01_macro_libref`          | `sasjs/core` macro conventions: `/*/STORE SOURCE*/`, `%mend <name>`, `%local` |
| `02_proc_append_debug`     | PROC APPEND silent-column-mismatch failure mode; what `FORCE` does and doesn't catch |
| `03_logistic_event`        | PROC LOGISTIC event pinning (`descending` / `event=`), `CLASS`, `ODS OUTPUT OddsRatios=` |

Each prompt file has YAML frontmatter with an `id`, the list of regex
`expected_patterns` the response must contain, and a `min_word_count` floor
to catch truncated responses. The prompt body follows the frontmatter. The
runner compiles each pattern via `re.search` — case-insensitive matching is
on individual patterns that need it (`(?i)`).

**Passing does not mean the SAS code is correct.** Pattern matching catches
structural errors — a rule might produce syntactically-plausible-but-
semantically-wrong code and still pass. Read `docs/EVALS.md` for the
architectural stance on this.

## How to add a new prompt

1. Drop a new `NN_short_name.md` file into `evals/prompts/`.
2. Give it frontmatter with:
   - `id` matching the filename stem
   - `domain` (one-line free text)
   - `expected_patterns` (list of Python regex strings)
   - `min_word_count` (integer; 50 is a reasonable floor)
3. Write the prompt body after the frontmatter.
4. Run the prompt in a fresh Claude Code session and save the reply to
   `evals/transcripts/<id>.txt`.
5. Run the harness.

Keep patterns conservative — prefer matching structural tokens (`%mend \w+;`)
over prose (`"remember to use..."`). The latter will drift with the model.
