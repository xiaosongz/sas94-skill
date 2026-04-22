# Evaluation harness

This directory holds a small regression-baseline eval for `sas94-skill`. It
answers one question: does the skill, loaded into Claude as a system message,
still produce SAS code that carries the structural markers the rules and
idioms in `references/*.md` demand?

The harness is intentionally small. Three prompts. Regex pattern matching on
the response. No semantic SAS verification. Its job is to catch a regression
where a reference-file edit quietly removes a guardrail — not to grade
correctness.

## How to run

From the repo root:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
uv --directory pipeline run python ../evals/run_evals.py
```

The runner uses the pipeline's `uv` environment so it can resolve the
`anthropic` dependency. Exit codes:

- `0` — every prompt matched every expected pattern and cleared the
  `min_word_count` floor.
- `1` — at least one prompt failed a check.
- `2` — `ANTHROPIC_API_KEY` is unset.

## Cost estimate

One run costs roughly **$0.50–$1.00** the first time and **~$0.10** on every
follow-up run within the prompt-cache TTL.

Breakdown:

- System message: `SKILL.md` + 13 reference files ≈ 60–80k input tokens.
- First prompt pays full input price (`$5 / 1M tokens` on Opus 4.7):
  ~80k × $5 / 1M ≈ $0.40 just for the cache write.
- Prompts 2 and 3 hit the cache at ~10% of the input rate: ~80k × $0.50 / 1M
  ≈ $0.04 each.
- Output is short (a SAS snippet plus a few paragraphs): ~500–1000 tokens at
  `$25 / 1M` ≈ $0.02 per prompt.

Total first run: ~$0.50. Subsequent runs within ~5 minutes of each other:
~$0.10. See the `cache_control: {"type": "ephemeral"}` marker on the system
message in `run_evals.py` — that is what triggers prompt caching. The
Anthropic Prompt Caching docs spell out the 5-minute TTL and pricing
mechanics.

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
4. Run the harness. The new prompt is picked up by the `prompts/*.md` glob.

Keep patterns conservative — prefer matching structural tokens (`%mend \w+;`)
over prose (`"remember to use..."`). The latter will drift with the model.

## Notes on caching

Prompt caching is handled automatically by the `cache_control` marker on the
system message. The TTL is 5 minutes (`ephemeral`), so consecutive runs of
the harness share one cache write. If you run the suite once, wait an hour,
and rerun, the first prompt will pay the full cache-write cost again.

The SDK reports cache hits via `response.usage.cache_read_input_tokens`; the
current runner does not surface that metric in the results table but you can
add it if you want to verify the caching is working on your run.
