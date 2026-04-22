# Contributing to sas94-skill

## Scope

Content contributions to `references/*.md` and `assets/*.sas` are the
primary contribution path. Pipeline extractor changes
(`pipeline/extractors/`) are welcome but must be tested against the
pinned `sasjs/lint` and `sasjs/core` SHAs recorded in
`pipeline/sources.yaml` — changing a SHA is a separate, reviewed PR.

### Frontmatter conventions

Every `references/*.md` file carries this YAML frontmatter block:

```yaml
---
title: <topic>
scope: <one-sentence description of what this file covers>
loaded_when: <routing triggers as quoted keywords or prose>
last_reviewed: YYYY-MM-DD
reviewer: <GitHub handle>
---
```

`loaded_when` is **documentation for human reviewers**, not a Claude
Code harness signal. The harness reads only `SKILL.md`'s
`description:` and `allowed-tools:` at activation time; reference files
are fetched on demand when `SKILL.md`'s Reference Routing table (or
Claude's judgement) calls for them by path. `loaded_when` exists so
that a future reviewer scanning a reference file can see at a glance
what triggers are supposed to route work into that file.

## Workflow

1. **Fork** the repo to your GitHub account.
2. **Branch per reference-file change**. Name the branch after the target
   file and the change kind:
   - `feat/macros-add-quoting-rule`
   - `fix/data-step-merge-overwrite-example`
   - `docs/proc-sql-seed`
3. **Edit the target reference file**. Every new Rule or Idiom MUST carry
   a `Source:` URL on the line immediately following the heading. The
   pre-commit hook (added in Task 7) will reject headings without
   sources.
4. **Regenerate the audit trail** if you added or removed a Rule/Idiom:
   ```bash
   uv --directory pipeline run python make_provenance.py > docs/rule-provenance.md
   ```
5. **Regenerate the coverage matrix** if you populated a previously-stub
   reference file:
   ```bash
   uv --directory pipeline run python make_coverage.py > docs/coverage-matrix.md
   ```
6. **Open a PR** against `main`. Fill in the PR template (below).

## PR Template Checklist

Copy this checklist into your PR body:

```markdown
- [ ] Every new `### Rule` or `### Idiom` heading has a `Source:` URL
      within 5 lines after the heading
- [ ] CORRECT and WRONG code blocks are both present for each Rule
      (CORRECT / WRONG labels inside the `sas` fence)
- [ ] Source URL resolves (CI runs a HEAD request against every URL in
      `docs/rule-provenance.md`)
- [ ] Rule points to a real `sasjs/lint` / `sasjs/core` / SAS 9.4
      documentation page or a hand-transcribed `pipeline/manual/*.md`
      file — no fabricated citations
- [ ] `docs/rule-provenance.md` regenerated (if any Rule / Idiom added,
      removed, or renamed)
- [ ] `docs/coverage-matrix.md` regenerated (if file coverage status
      changed)
- [ ] `last_reviewed` in the reference-file frontmatter updated to
      today's ISO date
- [ ] Pre-commit hook passes locally (`pre-commit install && pre-commit run --all-files`)
```

## Issue Template — Rule Dispute

When filing an issue to dispute an existing Rule, include:

```markdown
**Rule location**: `references/<file>.md` §<section> Rule N

**Current claim**: <paste the one-line rule heading>

**Alternative evidence**:
- URL to SAS 9.4 official documentation, SUGI / PharmaSUG / SAS Global
  Forum paper, or upstream `sasjs` commit that supports a different
  position.
- Or: explain why the current source URL does not support the claim
  as written.

**SAS 9.4 reproducer** (5–15 lines, self-contained):
```sas
/* minimal program demonstrating the correct behavior */
data _null_;
  ...
run;
```

**Expected log / output**:
<paste the SAS log fragment or output that demonstrates the claim>
```

## Issue Template — New Rule Proposal

```markdown
**Target file**: `references/<file>.md`

**Proposed rule heading**: `### Rule N: <one-line claim>`

**Source URL** (must resolve):
https://github.com/... OR https://documentation.sas.com/... OR
https://www.lexjansen.com/...

**CORRECT example** (5–15 lines of SAS):
```sas
/* CORRECT */
...
```

**WRONG example** (5–15 lines of SAS):
```sas
/* WRONG — <one-line reason> */
...
```

**Silent vs. loud failure**: <which is it, and how does it manifest?>
```

## Review

Reviewers check:

- **Source URL resolves** and genuinely supports the claim (not
  adjacent-but-not-supporting documentation).
- **CORRECT / WRONG examples** are SAS 9.4-valid — not fabricated,
  not copy-pasted from a different dialect, not silently altered from the
  source.
- **File size budget** — keep each topic reference file at ≤8 Critical
  Rules and ~30 lines per rule. Split into a new reference file if the
  topic outgrows its scope. The only exception is
  `references/sas-master-reference.md`, which aggregates across topic
  files and is allowed to hold up to 20 cross-topic rules.
- **No placeholder text** — `TBD`, `fabricate`, `TODO (source pending)`,
  or empty `Source:` strings in a PR that claims to populate a rule.
- **Idempotence** — re-running `make_provenance.py` and
  `make_coverage.py` must produce byte-identical output. Do not edit
  `docs/rule-provenance.md` or `docs/coverage-matrix.md` by hand.

## Code of Conduct

Be technical. Be honest. Prefer evidence in this order:

1. `sasjs/lint` source TypeScript (the actual rule logic)
2. `sasjs/core` base macros (idiomatic SAS 9.4)
3. SAS 9.4 official documentation (`documentation.sas.com`)
4. SUGI / PharmaSUG / SAS Global Forum papers (`lexjansen.com`)
5. SAS-L archive or community forums (treat with skepticism)

Fabricated rules — claims that look reasonable but have no traceable
source — are the single most destructive contribution class. When in
doubt, open an issue instead of a PR.
