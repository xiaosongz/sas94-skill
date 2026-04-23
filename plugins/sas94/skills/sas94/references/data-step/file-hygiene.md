---
title: sasjs/lint file hygiene for .sas sources
loaded_when: '"sasjs/lint", linting, indentation, line length, tabs vs spaces, trailing whitespace, gremlin / non-printable characters, encoded password "{SAS001}" / "{SAS002}" / "{SASENC}".'
---

File-hygiene items from `sasjs/lint` v2.4.3. These are line-level
conventions — indentation, line length, whitespace, non-printables,
encoded passwords — that do not alter DATA-step semantics but do cause
review-time churn or invisible-byte bugs when left unchecked.

## Critical Rules

### Hygiene 1: Indent by a consistent multiple of spaces (default 2) — no ad-hoc indentation

`sasjs/lint indentationMultiple` fires when a line is indented by a
non-multiple of the configured width (default 2). Consistent indentation
makes DATA-step / macro nesting readable at a glance.

```sas
/* CORRECT - indented by 2 */
data out;
  set in;
  if x > 0 then y = log(x);
run;
```

```sas
/* WRONG - indented by 1 or 3 spaces */
data out;
 set in;
   if x > 0 then y = log(x);
run;
```

### Hygiene 2: Keep lines under the configured maximum length (default 300)

`sasjs/lint maxLineLength` flags any line exceeding the configured limit.
Long lines hide logic in horizontal scroll and break diff review. For
long variable lists, break after a comma; for long `where` clauses,
break after the logical operator.

```sas
/* CORRECT - wrap after comma / logical op */
data claims_2023;
  set raw.claims;
  where service_dt between '01JAN2023'd and '31DEC2023'd
    and paid_amt > 0
    and not missing(member_id);
run;
```

```sas
/* WRONG - one 300+ char line with all conditions inline */
data claims_2023; set raw.claims; where service_dt between '01JAN2023'd and '31DEC2023'd and paid_amt > 0 and not missing(member_id) and provider_npi ne '' and diagnosis_code in ('E11.9','I10','N18.3','J44.9'); run;
```

### Hygiene 3: Indent with spaces, never tab characters

`sasjs/lint noTabs` rejects any `\t` (ASCII 0x09). Tab rendering depends
on editor settings — what looks aligned on one machine is misaligned on
another and confuses diff tools.

```sas
/* CORRECT - two spaces */
data out;
  set in;
run;
```

```sas
/* WRONG - leading tab; noTabs fires */
data out;
	set in;
run;
```

### Hygiene 4: Strip trailing whitespace from every line

`sasjs/lint noTrailingSpaces` flags any line ending with one or more
spaces before the newline. Trailing spaces break `diff --word-diff` and
cause spurious merge conflicts.

```sas
/* CORRECT - no trailing space */
data out;
  set in;
run;
```

```sas
/* WRONG - trailing whitespace on code lines (invisible, but present)

   After the semicolon on each code line below, the source file carries
   trailing ASCII space characters (0x20). `sasjs/lint noTrailingSpaces`
   auto-fixes these. Git history diffs flood with whitespace-only churn
   when left in.
*/
%put 'hello';
%put 'world';
/* imagine two or more 0x20 bytes after each semicolon, before the newline */
```

### Hygiene 5: No "gremlin" non-printable characters

`sasjs/lint noGremlins` flags characters outside the standard printable
ASCII + allowed-list Unicode range. Invisible characters in a `where`
clause or string literal break equality compares at runtime with no log
diagnostic.

```sas
/* CORRECT - plain ASCII */
data out;
  set in;
  where member_id = 'A12345';
run;
```

```sas
/* WRONG - gremlin bytes inside the quoted string (invisible in most editors)

   The literal bytes between 'A' and '12345' below include U+FEFF (BOM,
   three bytes: EF BB BF) copied from an Excel export. `sasjs/lint noGremlins`
   flags the token; the WHERE clause silently fails to match cleanly-typed
   'A12345' rows.
*/
data out;
  set in;
  where member_id = 'A<U+FEFF>12345';   /* actual file would have invisible bytes */
run;
```

### Hygiene 6: Never commit encoded-password literals (`{SAS001}`, `{SAS002}`, `{SASENC}`)

`sasjs/lint noEncodedPasswords` fires on any line containing the
bracketed encoding markers. SAS encoded passwords are trivially
reversible — they are obfuscation, not encryption. Treat them as
plaintext for secret-management purposes.

```sas
/* CORRECT - read password from env or autoexec, never in source */
libname db oracle user=svc password="&env_db_pw" path=prod;
```

```sas
/* WRONG - committed to source; noEncodedPasswords fires */
libname db oracle user=svc password="{SAS002}D41D8CD98F00B204E9800998ECF8427E" path=prod;
```

## Silent Pitfalls

- **Trailing spaces / tabs / gremlins** — invisible-character bugs in
  `where` clauses and string literals. Enforce via `sasjs/lint`
  `noTabs`, `noTrailingSpaces`, `noGremlins` (Hygiene 3-5 above). A
  gremlin inside a string literal produces no log diagnostic; the
  predicate simply fails to match the clean-typed value.
- **Encoded passwords treated as secure** — `{SAS002}` is reversible.
  Source-committed credentials are plaintext for threat-model purposes.

## Anti-patterns (STOP signs)

- Mixed tab + space indentation in the same file — renders inconsistently
  across editors, breaks `diff` alignment.
- Committing any `{SAS001}` / `{SAS002}` / `{SASENC}` literal — rotate
  the credential and move the reference to an environment variable.
