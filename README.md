# sas94-skill

A [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skill for writing, reviewing, and debugging SAS 9.4 code with AI assistance.

**Status:** Design phase. See [`docs/design.md`](docs/design.md).

## Motivation

Biostatisticians and health-services researchers use SAS 9.4 daily. Current LLMs produce poor SAS code because SAS is underrepresented in training corpora. No Claude Code skill for SAS exists. This skill fills the gap.

## Planned architecture

- Thin router `SKILL.md` + on-demand `references/*.md` files per topic (DATA step, PROC SQL, macros, base procs, stat procs, hash, ODS, formats, functions, idioms)
- Rules distilled from MIT-licensed sources (`sasjs/lint`, `sasjs/core`) + transformative use of SAS 9.4 documentation

## Install (future)

Not yet published. See `docs/design.md` for planned install UX.

## License

MIT (pending).
