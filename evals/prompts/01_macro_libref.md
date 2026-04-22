---
id: 01_macro_libref
domain: macro / sasjs-core idiom
expected_patterns:
  - '/\*\s*STORE SOURCE\s*\*/'
  - '%mend\s+\w+\s*;'
  - '%local\b'
min_word_count: 50
---

Write a SAS macro that returns an unused libref name, following sasjs/core
conventions. Include the `%macro` signature with parenthesized parameters,
the `/*/STORE SOURCE*/` registration option, `%local` declarations for every
internal symbol, and close with a named `%mend <name>;`. Show a brief example
of how a caller would invoke it.
