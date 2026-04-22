---
id: 03_logistic_event
domain: PROC LOGISTIC event + ODS OUTPUT
expected_patterns:
  - '(?i)\bdescending\b|event\s*=\s*[''"]'
  - '(?i)ODS\s+OUTPUT\s+OddsRatios\s*='
  - '(?i)\bCLASS\s+sex\b'
  - '(?i)\bMODEL\s+died_30d\s*='
min_word_count: 50
---

Write PROC LOGISTIC code to model 30-day mortality on age, sex, and Charlson
comorbidity index. The outcome column is `died_30d` (0/1 numeric, 1 = died).
Age and Charlson are continuous; sex is categorical.

Requirements:

- Pin the event so the model predicts `P(died_30d = 1)`, not the default
  lowest-ordinal value
- Declare `sex` as categorical via `CLASS`
- Capture the odds-ratio estimates as a SAS dataset via `ODS OUTPUT`

Explain why pinning the event matters for PROC LOGISTIC and what happens if
you omit it.
