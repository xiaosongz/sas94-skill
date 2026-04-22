---
id: 02_proc_append_debug
domain: PROC APPEND shape mismatch
expected_patterns:
  - '\bFORCE\b'
  - '\b(keep=|rename=)'
  - '(silent|silently|missing|without warning|no warning)'
min_word_count: 50
---

I'm getting this error from PROC APPEND:

```
ERROR: Variable X in DATA set not in BASE set. No appending done.
```

Here's my call:

```sas
proc append base=claims data=claims_new;
run;
```

How do I fix this? Explain what's happening, what the `FORCE` option actually
does (and what it doesn't catch), and what I should do instead to make the
DATA dataset shape match the BASE dataset before appending. Call out the
silent-failure case where BASE has a column that DATA is missing.
