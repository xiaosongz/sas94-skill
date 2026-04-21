---
title: SAS 9.4 Claude Code Skill — Design Spec
date: 2026-04-21
author: Xiaosong Zhang
status: draft
related: truveta-prose-skill (pattern blueprint)
---

# SAS 9.4 Claude Code Skill — Design Spec

## Purpose

Build a public open-source Claude Code skill that helps LLMs (Claude, and by extension any skill-compatible AI agent) write, review, and debug SAS 9.4 code with grammar and idiom fidelity comparable to AI assistance for mainstream languages.

## Problem

Biostatisticians, health services researchers, and pharma analysts use SAS 9.4 daily. Current LLMs produce poor SAS code because SAS is underrepresented in training corpora. Existing ecosystem:

- **Zero Claude Code skills for SAS** (confirmed 2026-04-21 survey)
- **Zero Cursor / Copilot rules files for SAS** on GitHub
- **SAS Viya Copilot** exists but requires Viya license — inaccessible to the SAS 9.4 user base
- `sasjs/lint` (16 rules) and `sasjs/core` (129⭐ MIT) provide machine-readable rule sources that no AI tooling has consumed yet

The space is nearly empty for SAS 9.4. This skill fills the gap.

## Design Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Distribution | Public MIT open-source | Widest reach, matches Truveta precedent |
| Documentation strategy | Distillation + URL routing, not verbatim embed | SAS ToU prohibits redistribution ($75K/instance penalty); transformative use defensible |
| Scope | Single skill, hierarchical progressive disclosure | Router SKILL.md + on-demand reference files fits within context budgets |
| Content sourcing | Hybrid pipeline + colleague review | Pipeline drafts reference files, SAS-expert colleagues review per-file PRs |
| v1 coverage | Broad (DATA step, macros, PROC SQL, base procs, stat procs, hash, ODS, formats, functions, idioms) | Colleagues' claims/observational workload + widest audience |
| Validation | Zero runtime dependencies; guidance-only (no sasjs/lint, no SASPy MCP in v1) | Ship fast, zero-install friction; add lint hook as v1.1 flag |

## Architecture

### File tree

```
sas94-skill/
├── SKILL.md                              # Thin router (~8–10KB). Always in context.
├── README.md                             # Install + usage, public-facing
├── LICENSE                               # MIT
├── permissions.json                      # File access scope
├── assets/
│   ├── data-step-template.sas
│   ├── proc-sql-template.sas
│   ├── macro-template.sas
│   └── analysis-template.sas
├── references/                           # Loaded on-demand per routing table
│   ├── sas-master-reference.md           # Grammar overview + top 30 pitfalls (~15KB)
│   ├── data-step.md                      # MERGE/BY/first./last., retain, arrays, PDV (~10KB)
│   ├── proc-sql.md                       # Joins, dedup, INTO lists, RESET (~8KB)
│   ├── macros.md                         # %let, %macro scope, quoting functions (~12KB)
│   ├── base-procs.md                     # FREQ, MEANS, UNIVARIATE, SORT, TRANSPOSE (~8KB)
│   ├── stat-procs.md                     # LOGISTIC, GLM, MIXED, GENMOD, SURVEY* (~10KB)
│   ├── hash-tables.md                    # declare hash, hashiter (~8KB)
│   ├── ods-and-output.md                 # ODS OUTPUT, RTF, EXCEL, graphics (~6KB)
│   ├── formats-informats.md              # PROC FORMAT, date/time, picture fmts (~5KB)
│   ├── functions-reference.md            # Function cheatsheet by category (~8KB)
│   └── idioms-from-lexjansen.md          # Real-world idioms distilled from SUGI (~6KB)
├── pipeline/                             # Build-time only. Not shipped to users.
│   ├── fetch_github.py
│   ├── fetch_sas_docs.py
│   ├── fetch_lexjansen.py
│   ├── fetch_community.py
│   ├── distill_rules.py
│   ├── sources.yaml
│   ├── extractors/
│   │   ├── sasjs_lint.py
│   │   ├── sasjs_lint_specs.py
│   │   ├── sasjs_core_lint.py
│   │   ├── sasjs_core_doxygen.py
│   │   ├── sasjs_core_macros.py
│   │   └── sas_html.py
│   ├── manual/
│   │   └── gwu-data-mining-5-items.md
│   └── cache/                            # gitignored; github/, docs/, lexjansen/, community/
└── docs/
    ├── CONTRIBUTING.md
    ├── coverage-matrix.md                # Auto-generated: which files have which sections
    └── rule-provenance.md                # Auto-generated: every rule → source URL
```

### Reference routing table (lives in SKILL.md)

| Task / Trigger Phrase | Load Reference | Also Load If |
|-----------------------|---------------|--------------|
| New `.sas` file, study program skeleton | `sas-master-reference.md` | + domain file per section |
| "MERGE", "BY processing", "first.", "last.", "retain", "array", "PDV" | `data-step.md` | `functions-reference.md` if fns involved |
| "PROC SQL", "join claims", "dedup", "INTO :macvar" | `proc-sql.md` | `macros.md` if INTO drives macro |
| "%macro", "%let", "%sysfunc", quoting error, `&&var`, symget/symput | `macros.md` | `sas-master-reference.md` for scope rules |
| PROC FREQ / MEANS / UNIVARIATE / SORT / TRANSPOSE / REPORT | `base-procs.md` | `ods-and-output.md` if capturing output |
| PROC LOGISTIC / GLM / MIXED / GENMOD / SURVEY* / LIFETEST | `stat-procs.md` | `ods-and-output.md` for ODS OUTPUT |
| "hash join", "hash lookup", `declare hash`, `definekey`, `hashiter` | `hash-tables.md` | `data-step.md` for DATA-step context |
| ODS RTF/EXCEL/PDF, ODS OUTPUT, ODS GRAPHICS, GTL | `ods-and-output.md` | `stat-procs.md` if capturing proc output |
| PROC FORMAT, date/time fns, picture formats, `input()`/`put()` | `formats-informats.md` | `functions-reference.md` |
| Function signature lookup, date arithmetic, string fns | `functions-reference.md` | — |
| Unknown/novel, "how do SAS programmers do X" | `idioms-from-lexjansen.md` | + best-match topic file |

Auto-activation triggers (SKILL.md frontmatter `description:`): file open/edit `*.sas`, `*.sas7bcat`; prompts containing "SAS", "DATA step", "PROC SQL", "%macro", "claims merge", "ODS output", etc.

Load budget discipline:
- SKILL.md always loaded (~10KB)
- Max 2 reference files per task (~20KB typical)
- Cap total skill context < 30KB unless user explicitly requests deep dive

### Reference file template

Every `references/*.md` follows this skeleton:

```markdown
---
title: <topic>
scope: <one-sentence what this file covers>
loaded_when: <routing triggers>
last_reviewed: YYYY-MM-DD
reviewer: <colleague handle>
---

## Overview
<2-3 sentences>

## Critical Rules
### Rule N: <one-line imperative rule>
<Why — 1-2 sentences>
```sas
/* CORRECT */
<minimal example>
```
```sas
/* WRONG - <what fails> */
<anti-example>
```
Source: <documentation URL or GitHub repo + path>

## Canonical Idioms
<named recipes. Each = name + purpose + code block + source URL>

## Function / Statement Quick Ref
| Name | Syntax | Purpose | Common mistake | Doc URL |
|------|--------|---------|----------------|---------|

## Silent Pitfalls (optional — populate if source material exists)

## Anti-patterns (STOP signs) (optional — populate if source material exists)

## See Also
```

Tiering:

- **REQUIRED**: Frontmatter, Overview, Critical Rules (≥1), Canonical Idioms (≥2), Function/Statement Quick Ref, See Also
- **OPTIONAL**: Silent Pitfalls, Anti-patterns — populate when source material exists; do NOT fabricate

Consistency rules:
- Max 8 Critical Rules per file (otherwise split)
- Every rule has CORRECT + WRONG code block
- Every rule has source URL (feeds `docs/rule-provenance.md`)
- Code blocks use `sas` fence, < 15 lines each
- No rule text > ~30 lines including examples

## Pipeline (build-time only)

### Source tier table

| Tier | Source | License | Feeds | Phase 1 action |
|------|--------|---------|-------|----------------|
| 1 | `sasjs/lint` (MIT, 15 rules + spec.ts examples) | MIT | Critical Rules, Silent Pitfalls, Anti-patterns | **Clone, extract verbatim** |
| 1 | `sasjs/core` (MIT, 129⭐, Doxygen discipline + ~150 base macros) | MIT | Canonical Idioms, Quick Ref, Critical Rules (5-8) | **Clone, extract machine-readable rules + idiom corpus** |
| 1 | `jphall663/GWU_data_mining` (MIT, 241⭐ but only 2 SAS files) | MIT | 5 specific items (LAG trap, MERGE overwrite, PROC APPEND, SQL join progression, macro-quote rule) | **Manual transcribe, no clone** |
| 1 (legal track) | `HHS-AHRQ/MEPS` (no LICENSE, 187⭐, survey procs) | public domain under 17 USC 105 **likely but unlabeled** | Survey-proc idioms in `stat-procs.md` | **Open GitHub issue + email AHRQ requesting LICENSE; use as inspiration only while pending** |
| 2 | `documentation.sas.com /doc/en/` | SAS ToU (transformative use only) | Function/Statement Quick Ref | Scrape with httpx+bs4+requests-cache via `/doc/en/` path (robots.txt-permitted); use `xisDoc-*` selectors |
| 2 | `lexjansen.com` SUGI PDFs | Author-owned, freely downloadable | Silent Pitfalls, Anti-patterns, hash deep-dives | Download + markitdown → text; Paul Dorfman hash, Kirk Paul Lafler PROC SQL, macro quoting papers |
| 3 | SAS Communities + Stack Overflow `sas` tag | Varies; attribution required | Silent Pitfalls (community-sourced flag) | Tertiary, case-by-case |
| Skip | `sassoftware/learning-sas-by-example-2nd` (Apache 2.0, code-only, 12% comment density) | Apache 2.0 | — | Optional CORRECT-code corpus only, do not use for prose |
| Skip | `phuse-org/phuse-scripts` (MIT, 124⭐, 90% CDISC) | MIT | — | Skip for general skill; revisit for optional pharma extension in v2 |

### Build-time tooling

- All pipeline scripts run in Claude Code session (me + subagents). **Zero Claude API spend.** Extraction = session time + Python via `uv`.
- HTTP scraping library stack: `httpx[asyncio]` + `beautifulsoup4[lxml]` + `requests-cache` (SQLite backend)
- Rate limit: 1 req/sec semaphore, exponential backoff on 429/5xx
- User-Agent: `"SAS-Doc-Ingester/1.0 (research pipeline; contact: <email>)"`
- Path: `/doc/en/` default (explicitly permitted by robots.txt)
- Extraction selectors (from SAS doc HTML): `div.xisDoc-syntaxSimple`, `div.xisDoc-requiredArgGroup`, `div.xisDoc-exampleBlock`, `div.xisDoc-seeAlsoList`, `p.xisDoc-shortDescription`, `h1.xisDoc-title`

### GitHub-first build order

Phase 1 ships WITHOUT doc scraping. Reference files built from MIT GitHub sources alone:

1. Extract all 15 `sasjs/lint` rules → seed `sas-master-reference.md` Critical Rules + distribute to file-specific rules
2. Extract `sasjs/core` `.sasjslint` config + Doxygen template → seed Canonical Idioms, Critical Rules across `macros.md`, `data-step.md`
3. Hand-transcribe 5 items from `jphall663/GWU_data_mining`
4. Phase 1 colleague review per-file
5. Phase 2 fills Function/Statement Quick Ref from SAS doc scrape (targeted, not exhaustive)
6. Phase 2+ fills Silent Pitfalls/Anti-patterns from lexjansen PDFs (Paul Dorfman hash, Kirk Paul Lafler PROC SQL, macro quoting papers)

### Per-file PR workflow

- `pipeline/distill_rules.py --target hash-tables.md` generates draft
- Bot opens PR per draft with coverage diff + source URL list + reviewer checklist
- Colleague verifies each rule's source URL, fixes fabrications, marks PR ready
- `docs/rule-provenance.md` auto-updates post-merge

### Pipeline invariants

- No verbatim SAS-docs passages > 90 words in any reference file (transformative use guardrail)
- Every claim carries `Source:` URL; pre-commit hook greps for it on every Rule/Idiom header
- `make_coverage.py` regenerates `docs/coverage-matrix.md` post-merge
- Pipeline scripts are build-only, not shipped — `.skillignore` excludes `pipeline/` at install

## Distribution + Install

| Concern | Choice |
|---------|--------|
| Repo name | `sas94-skill` |
| License | MIT |
| Hosting | `github.com/xiaosongz/sas94-skill` |
| Install Option A | `git clone` into `.claude/skills/sas94` (per-project) |
| Install Option B | `git clone` to `~/skills/`, symlink into projects |
| Install Option C (v1.1) | Claude Code plugin marketplace `/plugin install sas94` |
| Versioning | SemVer, git tags (`v0.1.0` Phase 1, `v1.0.0` all references populated) |

`permissions.json`:

```json
{
  "read": ["*.sas", "*.sas7bcat", "*.sas7bdat"],
  "write": ["*.sas"],
  "bash": { "allow": [], "deny": ["rm -rf", "git push --force"] }
}
```

## Validation + Maintenance

### Pre-commit hooks

- Every `references/*.md` rule must have `Source:` URL line — grep-enforced
- `docs/coverage-matrix.md` regenerated, diff must be empty before commit
- `markdownlint-cli2` with code-fence relaxations
- YAML frontmatter validity

### GitHub Actions CI

- `validate-sources.yml`: weekly cron; fetch every `Source:` URL; fail on 404 (SAS URL rot detection)
- `lint-markdown.yml`: per-file size cap (warn > 20KB, hard fail > 40KB)
- `check-skill-load.yml`: parse SKILL.md frontmatter and routing table syntax

### Maintenance cadence

- SAS 9.4 in maintenance mode (last Mx release 2024)
- `sasjs/lint` + `sasjs/core` pulled quarterly for new rules
- Annual full-pipeline re-run, diff + review

### Contribution workflow

`docs/CONTRIBUTING.md` specifies:
- Fork → branch per reference file change
- PR template requires reviewer checklist (URL resolves, source backs claim, CORRECT+WRONG examples present, ≤8 rules per file)
- Issue template for rule disputes requires alternative evidence URL + SAS reproducer

### Rule provenance audit trail

`docs/rule-provenance.md` auto-generated per merge:

```markdown
| File | Section | Rule # | Claim | Source | Last verified |
|------|---------|:-----:|-------|--------|:------------:|
| macros.md | Critical Rules | 1 | Every %macro must have () | sasjs/lint hasMacroParentheses | 2026-04-21 |
```

### Dog-fooding test plan

Week 1 post Phase 1:
- Install on user + 2–3 colleagues' machines
- Run on 5 real workloads from OLIVE / Medicaid claims analyses
- Track false-positives + false-negatives → file issues → feed Phase 2

## Versioning semantics

- **v0.x.y** = pre-release. "Required" sections in the reference template may be stubbed with `TODO (source pending)` as long as the stub is explicit and not fabricated content. Acceptable for early adoption and dog-fooding.
- **v1.0.0** = every `references/*.md` has all REQUIRED sections populated from verified sources (Overview, Critical Rules, Canonical Idioms, Function/Statement Quick Ref, See Also).
- **v1.x** = additions to OPTIONAL sections (Silent Pitfalls, Anti-patterns), plus net-new idioms.

## Phase 1 completion criteria (v0.1.0 tag)

1. SKILL.md router + routing table complete for all 11 reference files
2. Critical Rules + Silent Pitfalls for `macros.md` + `data-step.md` sourced 100% from `sasjs/lint` + `sasjs/core`
3. Canonical Idioms for `data-step.md` + `proc-sql.md` seeded from `sasjs/core` base macros + 5 GWU items
4. Function/Statement Quick Ref marked `TODO (source pending)` rather than fabricated
5. `permissions.json`, `.skillignore`, pre-commit hooks, CI workflows committed
6. `README.md` + `docs/CONTRIBUTING.md` + `docs/rule-provenance.md` populated
7. Tagged `v0.1.0`, dog-fooded internally before public announcement

## Out of Scope (explicit non-goals)

- SAS Viya features (no Viya in v1)
- sasjs/lint runtime integration (v1.1 optional flag, not v1)
- SASPy / MCP server for live code execution (never — security surface + user install burden)
- CDISC/ADaM pharma-specific rules (v2 optional extension if demand)
- Multi-language polyglot support (skill is SAS-only; R/Python/Stata users have own skills)
- Real-time SAS log parsing (scope creep; out of v1)

## Risks + Mitigations

| Risk | Likelihood | Mitigation |
|------|-----------|-----------|
| SAS URL rot breaks `Source:` links | High (SAS moved docs before) | Weekly CI validates all URLs; provenance table enables bulk fix |
| SAS Institute issues takedown over doc scraping | Low (transformative use, /doc/en/ path permitted) | Keep extracts < 90 words verbatim; fallback to URL-only if challenged |
| Colleague review bandwidth insufficient | Medium | Per-file PRs kept < 30 min review; publish review queue in `docs/` for asynchronous reviewer pool |
| LLM hallucinates rules not in sources | Medium | Pre-commit hook requires `Source:` URL; PR reviewer rejects unsourced |
| `sasjs/lint` rule changes break our extraction | Low | Pin SHA per release; quarterly pull with diff review |
| MEPS license never clarified | Medium | Use as inspiration only until then; fallback to lexjansen papers for survey idioms |

## Open Questions

- Email address for SAS User-Agent header (need non-personal inbox)
- Whether `truveta-prose-skill` pattern table in README should cite this skill as sibling project post-launch
- Whether v1.1 should add `sasjs-lint` feedback-loop flag or focus on reference-file completeness first

## References

- Pattern blueprint: `/Users/xiaosong/git/truveta-prose-skill/`
- Research agent transcripts: in session 2026-04-21
- SAS documentation entry point: https://documentation.sas.com/doc/en/pgmsascdc/9.4_3.5/home.htm
- `sasjs/lint`: https://github.com/sasjs/lint
- `sasjs/core`: https://github.com/sasjs/core
- `HHS-AHRQ/MEPS`: https://github.com/HHS-AHRQ/MEPS (license pending)
- `lexjansen.com` SUGI archive: https://www.lexjansen.com
