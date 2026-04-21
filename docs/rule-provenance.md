# Rule Provenance

Audit trail for every `### Rule` and `### Idiom` heading in `references/*.md`. Each row records the rule's source URL and the `last_reviewed` date from the reference file's frontmatter. This file is auto-generated — do not edit by hand.

Regenerate after editing any reference file:

```bash
uv --directory pipeline run python make_provenance.py > docs/rule-provenance.md
```

| File | Section | # | Claim | Source | Last verified |
|------|---------|---|-------|--------|---------------|
| data-step.md | Canonical Idioms | idiom | `mf_nobs` — observation-count one-liner for open code | https://github.com/sasjs/core/blob/3a54b9c796c0bfe477d1aefc1e22b9ff9f2c96c2/base/mf_nobs.sas | 2026-04-21 |
| data-step.md | Canonical Idioms | idiom | Guarded predicate macro for DATA-step assertions | https://github.com/sasjs/core/blob/3a54b9c796c0bfe477d1aefc1e22b9ff9f2c96c2/base/mp_assertdsobs.sas | 2026-04-21 |
| data-step.md | Canonical Idioms | idiom | LAG missing-value trap (GWU §1) | https://github.com/jphall663/GWU_data_mining — hand-transcribed in `pipeline/manual/gwu-data-mining-5-items.md`. | 2026-04-21 |
| data-step.md | Canonical Idioms | idiom | Macro resolution and quote semantics (GWU §5) | https://github.com/jphall663/GWU_data_mining — hand-transcribed in `pipeline/manual/gwu-data-mining-5-items.md`. | 2026-04-21 |
| data-step.md | Canonical Idioms | idiom | MERGE overwrite trap (GWU §2) | https://github.com/jphall663/GWU_data_mining — hand-transcribed in `pipeline/manual/gwu-data-mining-5-items.md`. | 2026-04-21 |
| data-step.md | Canonical Idioms | idiom | PROC APPEND variable-shape rules (GWU §3) | https://github.com/jphall663/GWU_data_mining — hand-transcribed in `pipeline/manual/gwu-data-mining-5-items.md`. | 2026-04-21 |
| data-step.md | Canonical Idioms | idiom | SQL join vs MERGE distinction (GWU §4) | https://github.com/jphall663/GWU_data_mining — hand-transcribed in `pipeline/manual/gwu-data-mining-5-items.md`. | 2026-04-21 |
| data-step.md | Critical Rules | 1 | Indent by a consistent multiple of spaces (default 2) — no ad-hoc indentation | https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/line/indentationMultiple.ts | 2026-04-21 |
| data-step.md | Critical Rules | 2 | Keep lines under the configured maximum length (default 300) | https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/line/maxLineLength.ts | 2026-04-21 |
| data-step.md | Critical Rules | 3 | Indent with spaces, never tab characters | https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/line/noTabs.ts | 2026-04-21 |
| data-step.md | Critical Rules | 4 | Strip trailing whitespace from every line | https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/line/noTrailingSpaces.ts | 2026-04-21 |
| data-step.md | Critical Rules | 5 | No "gremlin" non-printable characters | https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/line/noGremlins.ts | 2026-04-21 |
| data-step.md | Critical Rules | 6 | Never commit encoded-password literals (`{SAS001}`, `{SAS002}`, `{SASENC}`) | https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/line/noEncodedPasswords.ts | 2026-04-21 |
| macros.md | Canonical Idioms | idiom | `%local` discipline — declare every non-parameter symbol at top | https://github.com/sasjs/core/blob/3a54b9c796c0bfe477d1aefc1e22b9ff9f2c96c2/base/mp_hashdataset.sas | 2026-04-21 |
| macros.md | Canonical Idioms | idiom | `/*/STORE SOURCE*/` inline option — one-line signature close | https://github.com/sasjs/core/blob/3a54b9c796c0bfe477d1aefc1e22b9ff9f2c96c2/base/mf_abort.sas | 2026-04-21 |
| macros.md | Canonical Idioms | idiom | Guarded-execution `iftrue=` parameter | https://github.com/sasjs/core/blob/3a54b9c796c0bfe477d1aefc1e22b9ff9f2c96c2/base/mp_hashdataset.sas | 2026-04-21 |
| macros.md | Canonical Idioms | idiom | Positional-required + keyword-optional parameter pattern | https://github.com/sasjs/core/blob/3a54b9c796c0bfe477d1aefc1e22b9ff9f2c96c2/base/mf_existds.sas | 2026-04-21 |
| macros.md | Critical Rules | 1 | Every `%macro` signature must carry parentheses `()` | https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/file/hasMacroParentheses.ts | 2026-04-21 |
| macros.md | Critical Rules | 2 | Close every `%mend` with its macro name | https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/file/hasMacroNameInMend.ts | 2026-04-21 |
| macros.md | Critical Rules | 3 | No nested `%macro` definitions | https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/file/noNestedMacros.ts | 2026-04-21 |
| macros.md | Critical Rules | 4 | Strict macro-definition syntax — no spaces inside parameter names or invalid op… | https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/file/strictMacroDefinition.ts | 2026-04-21 |
| macros.md | Critical Rules | 5 | Every macro file starts with a Doxygen header (`@file`, `@brief`, `@param`, `@v… | https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/file/hasDoxygenHeader.ts | 2026-04-21 |
| macros.md | Critical Rules | 6 | Macros that are shared, stored, or security-sensitive carry required options (`… | https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/file/hasRequiredMacroOptions.ts | 2026-04-21 |
| sas-master-reference.md | Critical Rules | 1 | Every `%macro` signature must carry parentheses `()` | https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/file/hasMacroParentheses.ts | 2026-04-21 |
| sas-master-reference.md | Critical Rules | 2 | Close every `%mend` with its macro name | https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/file/hasMacroNameInMend.ts | 2026-04-21 |
| sas-master-reference.md | Critical Rules | 3 | Never nest `%macro` definitions | https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/file/noNestedMacros.ts | 2026-04-21 |
| sas-master-reference.md | Critical Rules | 4 | Use strict macro-definition syntax — no whitespace in parameter names, no unkno… | https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/file/strictMacroDefinition.ts | 2026-04-21 |
| sas-master-reference.md | Critical Rules | 5 | Every `.sas` file begins with a Doxygen header | https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/file/hasDoxygenHeader.ts | 2026-04-21 |
| sas-master-reference.md | Critical Rules | 6 | Security-sensitive or shared macros carry required options (`SECURE`, `STORE SO… | https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/file/hasRequiredMacroOptions.ts | 2026-04-21 |
| sas-master-reference.md | Critical Rules | 7 | Indent by a consistent multiple of spaces (default 2) | https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/line/indentationMultiple.ts | 2026-04-21 |
| sas-master-reference.md | Critical Rules | 8 | Keep lines under the configured maximum length (default 300) | https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/line/maxLineLength.ts | 2026-04-21 |
| sas-master-reference.md | Critical Rules | 9 | Indent with spaces, never tab characters | https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/line/noTabs.ts | 2026-04-21 |
| sas-master-reference.md | Critical Rules | 10 | Strip trailing whitespace from every line | https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/line/noTrailingSpaces.ts | 2026-04-21 |
| sas-master-reference.md | Critical Rules | 11 | No "gremlin" non-printable characters in source | https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/line/noGremlins.ts | 2026-04-21 |
| sas-master-reference.md | Critical Rules | 12 | Never commit encoded-password literals (`{SAS001}`, `{SAS002}`, `{SASENC}`) | https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/line/noEncodedPasswords.ts | 2026-04-21 |
| sas-master-reference.md | Critical Rules | 13 | Use Unix LF (\n) line endings, never CRLF | https://github.com/sasjs/lint/blob/6172b3a64125db6995509d4e5102f2c41b9e4294/src/rules/file/lineEndings.ts | 2026-04-21 |
| sas-master-reference.md | Critical Rules | 14 | LAG is queue-based — call unconditionally, gate usage afterwards (GWU §1) | https://github.com/jphall663/GWU_data_mining — hand-transcribed in `pipeline/manual/gwu-data-mining-5-items.md`. | 2026-04-21 |
| sas-master-reference.md | Critical Rules | 15 | MERGE silently overwrites same-named variables (GWU §2) | https://github.com/jphall663/GWU_data_mining — hand-transcribed in `pipeline/manual/gwu-data-mining-5-items.md`. | 2026-04-21 |
| sas-master-reference.md | Critical Rules | 16 | PROC APPEND variable-shape rules (GWU §3) | https://github.com/jphall663/GWU_data_mining — hand-transcribed in `pipeline/manual/gwu-data-mining-5-items.md`. | 2026-04-21 |
| sas-master-reference.md | Critical Rules | 17 | SQL join vs MERGE — different semantics, different failure modes (GWU §4) | https://github.com/jphall663/GWU_data_mining — hand-transcribed in `pipeline/manual/gwu-data-mining-5-items.md`. | 2026-04-21 |
| sas-master-reference.md | Critical Rules | 18 | Macro resolution and quote semantics (GWU §5) | https://github.com/jphall663/GWU_data_mining — hand-transcribed in `pipeline/manual/gwu-data-mining-5-items.md`. | 2026-04-21 |
| sas-master-reference.md | Critical Rules | 19 | Declare `%local` for every non-parameter symbol inside a macro | https://github.com/sasjs/core/blob/3a54b9c796c0bfe477d1aefc1e22b9ff9f2c96c2/base/mp_hashdataset.sas | 2026-04-21 |
| sas-master-reference.md | Critical Rules | 20 | Structure every macro signature as positional-required + keyword-optional, and… | https://github.com/sasjs/core/blob/3a54b9c796c0bfe477d1aefc1e22b9ff9f2c96c2/base/mf_existds.sas | 2026-04-21 |

Total rows: 43.
