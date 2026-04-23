# Coverage Matrix

Per-atom coverage report under the atom-based reference layout (`references/<topic>/<atom>.md`). Each non-index atom must carry either a `Critical Rules` section (with CORRECT + WRONG pair) or a `Canonical Idioms` section. `_index.md` atoms must carry a routing table or bullet list. Generated from `references/`; do not edit by hand.

Regenerate after editing any atom:

```bash
uv --directory pipeline run python make_coverage.py > docs/coverage-matrix.md
```

| Topic | Atom | Critical Rules | Canonical Idioms | Silent Pitfalls | Anti-patterns | Status |
|-------|------|----------------|------------------|------------------|----------------|--------|
| base-procs | _index | — | — | — | — | index |
| base-procs | file-io | yes | no | no | yes | populated |
| base-procs | proc-compare | yes | no | no | yes | populated |
| base-procs | proc-freq | yes | no | no | yes | populated |
| base-procs | proc-means | yes | no | no | yes | populated |
| base-procs | proc-print | yes | no | no | yes | populated |
| base-procs | proc-report | yes | no | no | yes | populated |
| base-procs | proc-sort | yes | no | no | yes | populated |
| base-procs | proc-transpose | yes | no | no | yes | populated |
| base-procs | proc-univariate | yes | no | no | yes | populated |
| base-procs | schema-utils | yes | no | no | yes | populated |
| data-step | _index | — | — | — | — | index |
| data-step | append | yes | no | yes | yes | populated |
| data-step | file-hygiene | yes | no | yes | yes | populated |
| data-step | lag | yes | no | yes | yes | populated |
| data-step | macro-quoting | yes | no | yes | yes | populated |
| data-step | merge | yes | no | yes | yes | populated |
| data-step | retain-pdv | yes | yes | yes | yes | populated |
| data-step | sql-vs-merge | yes | no | yes | yes | populated |
| data-step | where-vs-if | yes | no | yes | yes | populated |
| formats-informats | _index | — | — | — | — | index |
| formats-informats | date-formats | yes | no | yes | yes | populated |
| formats-informats | numeric-formats | yes | no | yes | yes | populated |
| formats-informats | proc-format | yes | no | yes | yes | populated |
| formats-informats | put-vs-input | yes | no | yes | yes | populated |
| functions-dates | _index | — | — | — | — | index |
| functions-dates | construction | yes | no | yes | yes | populated |
| functions-dates | date-arithmetic | yes | no | yes | yes | populated |
| functions-dates | datetime-parts | yes | no | yes | yes | populated |
| functions-dates | intnx-intck | yes | no | yes | yes | populated |
| functions-numeric | _index | — | — | — | — | index |
| functions-numeric | arithmetic | yes | no | yes | yes | populated |
| functions-numeric | arrays | yes | no | yes | yes | populated |
| functions-numeric | row-aggregates | yes | no | yes | yes | populated |
| functions-strings | _index | — | — | — | — | index |
| functions-strings | case-and-compare | no | no | yes | yes | stub |
| functions-strings | clean | yes | no | yes | yes | populated |
| functions-strings | concat | yes | yes | yes | yes | populated |
| functions-strings | parse | yes | yes | yes | yes | populated |
| hash-tables | _index | — | — | — | — | index |
| hash-tables | declare-and-length | yes | no | yes | yes | populated |
| hash-tables | find-check-rc | yes | no | yes | yes | populated |
| hash-tables | idioms | no | yes | no | no | populated |
| hash-tables | iteration | yes | no | yes | yes | populated |
| hash-tables | multidata | yes | no | yes | yes | populated |
| idioms-from-lexjansen | _index | — | — | — | — | index |
| idioms-from-lexjansen | hash-idioms | yes | yes | yes | yes | populated |
| idioms-from-lexjansen | macro-idioms | yes | yes | yes | yes | populated |
| idioms-from-lexjansen | sql-idioms | yes | yes | yes | yes | populated |
| macros | _index | — | — | — | — | index |
| macros | debugging | yes | no | yes | yes | populated |
| macros | definition-syntax | yes | yes | yes | yes | populated |
| macros | include-vs-macro | yes | no | yes | yes | populated |
| macros | scope-and-quoting | yes | no | yes | yes | populated |
| macros | sysfunc-and-eval | yes | yes | yes | yes | populated |
| ods-and-output | _index | — | — | — | — | index |
| ods-and-output | ods-destinations | yes | no | yes | yes | populated |
| ods-and-output | ods-graphics | yes | no | yes | yes | populated |
| ods-and-output | ods-listing | yes | no | yes | yes | populated |
| ods-and-output | ods-output-capture | yes | no | yes | yes | populated |
| ods-and-output | ods-select-exclude | yes | no | yes | yes | populated |
| proc-sql | _index | — | — | — | — | index |
| proc-sql | case-expressions | yes | no | yes | yes | populated |
| proc-sql | dedup | yes | no | yes | yes | populated |
| proc-sql | into-macvar | yes | no | yes | yes | populated |
| proc-sql | joins | yes | no | yes | yes | populated |
| proc-sql | reset-and-options | yes | no | yes | yes | populated |
| stat-procs | _index | — | — | — | — | index |
| stat-procs | proc-genmod | yes | yes | yes | yes | populated |
| stat-procs | proc-glm | yes | yes | yes | yes | populated |
| stat-procs | proc-lifetest | yes | yes | yes | yes | populated |
| stat-procs | proc-logistic | yes | yes | yes | yes | populated |
| stat-procs | proc-mixed | yes | yes | yes | yes | populated |
| stat-procs | proc-phreg | yes | yes | yes | yes | populated |
| stat-procs | proc-surveymeans | yes | yes | yes | yes | populated |

Atoms populated: 62 / 63; indexes populated: 12 / 12.
