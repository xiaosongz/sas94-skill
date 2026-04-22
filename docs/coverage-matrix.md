# Coverage Matrix

Per-reference-file coverage report — which template sections are populated vs. stubbed. Required sections must all be populated for a file to earn `populated` status; Silent Pitfalls and Anti-patterns are optional. Generated from `references/*.md`; do not edit by hand.

Regenerate after editing any reference file:

```bash
uv --directory pipeline run python make_coverage.py > docs/coverage-matrix.md
```

| File | Overview | Critical Rules | Canonical Idioms | Quick Ref | See Also | Silent Pitfalls | Anti-patterns | Required % | Status |
|------|----------|----------------|------------------|-----------|----------|------------------|----------------|------------|--------|
| base-procs.md | yes | yes | yes | yes | yes | yes | yes | 100% | populated |
| data-step.md | yes | yes | yes | yes | yes | yes | yes | 100% | populated |
| formats-informats.md | yes | yes | yes | yes | yes | yes | yes | 100% | populated |
| functions-dates.md | yes | yes | yes | yes | yes | yes | yes | 100% | populated |
| functions-numeric.md | yes | yes | yes | yes | yes | yes | yes | 100% | populated |
| functions-strings.md | yes | yes | yes | yes | yes | yes | yes | 100% | populated |
| hash-tables.md | yes | yes | yes | yes | yes | yes | yes | 100% | populated |
| idioms-from-lexjansen.md | yes | yes | yes | yes | yes | yes | yes | 100% | populated |
| macros.md | yes | yes | yes | yes | yes | yes | yes | 100% | populated |
| ods-and-output.md | yes | yes | yes | yes | yes | yes | yes | 100% | populated |
| proc-sql.md | yes | yes | yes | yes | yes | yes | yes | 100% | populated |
| sas-master-reference.md | yes | yes | yes | yes | yes | yes | yes | 100% | populated |
| stat-procs.md | yes | yes | yes | yes | yes | yes | yes | 100% | populated |

Populated: 13 / 13; Stubs: 0 / 13.
