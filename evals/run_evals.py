"""Pattern-check harness for the sas94-skill.

Reads Claude Code transcripts (plain .txt files produced by the user after
running each `evals/prompts/*.md` in a fresh Claude Code session with the
skill installed) and checks every transcript against the `expected_patterns`
and `min_word_count` from the matching prompt file's frontmatter.

This script does NOT call any LLM. The skill is evaluated as it ships —
inside Claude Code with on-demand reference-file routing — not simulated
via direct API calls.

Usage
-----

For each prompt under `evals/prompts/<id>.md`:

    1. Install the skill (see README.md § Installation).
    2. Open a fresh Claude Code session.
    3. Paste the prompt body from `evals/prompts/<id>.md` (everything after
       the second `---`).
    4. Save Claude's reply to `evals/transcripts/<id>.txt`.
    5. From the repo root, run:

           uv --directory pipeline run python ../evals/run_evals.py

Exit codes: 0 if every transcript matches every pattern; 1 on any miss;
2 if a transcript file is missing for a declared prompt.

Pattern matching catches structural / idiom-level errors — missing
`/*STORE SOURCE*/`, bare `%mend;`, wrong `event=` default, etc. It does
not verify SAS semantic correctness; a rule can produce
syntactically-plausible-but-semantically-wrong code and still pass.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
TRANSCRIPTS_DIR = Path(__file__).resolve().parent / "transcripts"


# ---------- Frontmatter parsing ---------------------------------------------

FRONTMATTER_RE = re.compile(
    r"\A---\n(?P<front>.*?)\n---\n(?P<body>.*)\Z",
    re.DOTALL,
)


@dataclass
class Prompt:
    id: str
    path: Path
    body: str
    expected_patterns: list[str]
    min_word_count: int


def parse_prompt(path: Path) -> Prompt:
    raw = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(raw)
    if not match:
        raise ValueError(f"{path}: missing YAML frontmatter block")

    front = match.group("front")
    body = match.group("body").strip()

    fields: dict[str, Any] = {}
    current_list_key: str | None = None
    for line in front.splitlines():
        if not line.strip():
            continue
        if line.startswith("  - ") and current_list_key is not None:
            item = line[4:].strip()
            if len(item) >= 2 and item[0] == item[-1] and item[0] in ("'", '"'):
                item = item[1:-1]
            fields[current_list_key].append(item)
            continue
        if ":" not in line:
            raise ValueError(f"{path}: unparseable frontmatter line: {line!r}")
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if value == "":
            fields[key] = []
            current_list_key = key
        else:
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
                value = value[1:-1]
            fields[key] = value
            current_list_key = None

    try:
        return Prompt(
            id=str(fields["id"]),
            path=path,
            body=body,
            expected_patterns=list(fields["expected_patterns"]),
            min_word_count=int(fields["min_word_count"]),
        )
    except KeyError as exc:
        raise ValueError(f"{path}: missing frontmatter key {exc!s}") from exc


# ---------- Evaluation ------------------------------------------------------


@dataclass
class Result:
    prompt_id: str
    word_count: int
    missing_patterns: list[str]
    below_word_floor: bool
    transcript_missing: bool = False

    @property
    def passed(self) -> bool:
        return (
            not self.transcript_missing
            and not self.missing_patterns
            and not self.below_word_floor
        )

    @property
    def status(self) -> str:
        if self.transcript_missing:
            return "NO_TRANSCRIPT"
        return "PASS" if self.passed else "FAIL"


def evaluate_transcript(prompt: Prompt, transcript_text: str) -> Result:
    word_count = len(transcript_text.split())
    missing = [
        pat
        for pat in prompt.expected_patterns
        if not re.search(pat, transcript_text)
    ]
    return Result(
        prompt_id=prompt.id,
        word_count=word_count,
        missing_patterns=missing,
        below_word_floor=word_count < prompt.min_word_count,
    )


# ---------- Entry point -----------------------------------------------------


def main() -> int:
    prompt_files = sorted(PROMPTS_DIR.glob("*.md"))
    if not prompt_files:
        sys.stderr.write(f"No prompt files found in {PROMPTS_DIR}\n")
        return 1

    prompts = [parse_prompt(p) for p in prompt_files]

    results: list[Result] = []
    any_missing = False
    for prompt in prompts:
        transcript_path = TRANSCRIPTS_DIR / f"{prompt.id}.txt"
        if not transcript_path.exists():
            any_missing = True
            results.append(
                Result(
                    prompt_id=prompt.id,
                    word_count=0,
                    missing_patterns=[],
                    below_word_floor=False,
                    transcript_missing=True,
                )
            )
            sys.stderr.write(
                f"MISSING transcript: {transcript_path.relative_to(REPO_ROOT)}\n"
            )
            continue

        transcript_text = transcript_path.read_text(encoding="utf-8")
        results.append(evaluate_transcript(prompt, transcript_text))

    header = "| prompt_id | status | word_count | missing_patterns |"
    sep = "|-----------|--------|------------|------------------|"
    print(header)
    print(sep)
    for r in results:
        if r.transcript_missing:
            missing = f"save Claude Code reply to evals/transcripts/{r.prompt_id}.txt"
        else:
            missing = ", ".join(r.missing_patterns) if r.missing_patterns else "-"
            if r.below_word_floor:
                missing = (
                    f"(below min word count) {missing}"
                    if r.missing_patterns
                    else "(below min word count)"
                )
        print(f"| {r.prompt_id} | {r.status} | {r.word_count} | {missing} |")

    if any_missing:
        return 2
    return 0 if all(r.passed for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
