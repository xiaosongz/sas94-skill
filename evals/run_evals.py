"""Evaluation harness for the sas94-skill.

Loads `SKILL.md` + every `references/*.md` as a cached system message, then
sends each prompt under `evals/prompts/*.md` to `claude-opus-4-7` via the
Anthropic SDK and checks the response for required regex patterns and a
minimum word count.

Run from the repo root:

    export ANTHROPIC_API_KEY=sk-ant-...
    uv --directory pipeline run python ../evals/run_evals.py

Exits 0 when every prompt matches every pattern and clears the min-word
floor; exits 1 on any miss; exits 2 when `ANTHROPIC_API_KEY` is unset.

Intentionally simple: no retries on API errors (traceback + fail), a 2-second
sleep between prompts so a 3-prompt run doesn't burst, and prompt caching on
the skill content so repeat runs within the cache TTL pay roughly 10% of the
first run's input cost. Pattern matching catches structural errors — it does
not verify SAS semantic correctness.
"""

from __future__ import annotations

import os
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import anthropic
except ImportError:  # pragma: no cover — surfaced to user
    sys.stderr.write(
        "The `anthropic` package is not installed. Run:\n"
        "    uv --directory pipeline sync\n"
    )
    raise

MODEL = "claude-opus-4-7"
MAX_TOKENS = 4000
SLEEP_BETWEEN_PROMPTS_S = 2

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_PATH = REPO_ROOT / "SKILL.md"
REFERENCES_DIR = REPO_ROOT / "references"
PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


# ---------- Frontmatter parsing ---------------------------------------------

# Prompt files are small and controlled; a stdlib-only YAML-ish parser is
# enough and avoids dragging PyYAML into the eval path.
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
            # Strip surrounding quotes if present.
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
            # List-valued key.
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


# ---------- Skill content loading -------------------------------------------


def load_skill_content() -> str:
    """Concatenate SKILL.md and all references/*.md into one system string.

    Order: SKILL.md first, then references/*.md sorted by filename. Files are
    separated by a clear delimiter so the model can route within the content
    the same way Claude Code would route by loading specific files.
    """
    parts: list[str] = []
    parts.append(f"=== SKILL.md ===\n\n{SKILL_PATH.read_text(encoding='utf-8')}")
    for ref in sorted(REFERENCES_DIR.glob("*.md")):
        parts.append(
            f"=== references/{ref.name} ===\n\n{ref.read_text(encoding='utf-8')}"
        )
    return "\n\n".join(parts)


# ---------- Evaluation ------------------------------------------------------


@dataclass
class Result:
    prompt_id: str
    word_count: int
    missing_patterns: list[str]
    below_word_floor: bool

    @property
    def passed(self) -> bool:
        return not self.missing_patterns and not self.below_word_floor

    @property
    def status(self) -> str:
        return "PASS" if self.passed else "FAIL"


def evaluate_response(prompt: Prompt, response_text: str) -> Result:
    word_count = len(response_text.split())
    missing = [
        pat
        for pat in prompt.expected_patterns
        if not re.search(pat, response_text)
    ]
    return Result(
        prompt_id=prompt.id,
        word_count=word_count,
        missing_patterns=missing,
        below_word_floor=word_count < prompt.min_word_count,
    )


def run_prompt(
    client: anthropic.Anthropic,
    skill_content: str,
    prompt: Prompt,
) -> Result:
    # System message uses the list-of-blocks form so we can attach
    # `cache_control` to the skill content. The 5-minute ephemeral TTL is
    # enough to keep all three prompts in one run on a single cache entry.
    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=[
            {
                "type": "text",
                "text": skill_content,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": prompt.body}],
    )
    text_parts = [b.text for b in response.content if b.type == "text"]
    response_text = "\n".join(text_parts)
    return evaluate_response(prompt, response_text)


# ---------- Entry point -----------------------------------------------------


def main() -> int:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.stderr.write(
            "Set ANTHROPIC_API_KEY (e.g. `export ANTHROPIC_API_KEY=...`)\n"
        )
        return 2

    prompt_files = sorted(PROMPTS_DIR.glob("*.md"))
    if not prompt_files:
        sys.stderr.write(f"No prompt files found in {PROMPTS_DIR}\n")
        return 1

    prompts = [parse_prompt(p) for p in prompt_files]
    skill_content = load_skill_content()
    client = anthropic.Anthropic()

    results: list[Result] = []
    for i, prompt in enumerate(prompts):
        sys.stderr.write(f"[{i + 1}/{len(prompts)}] {prompt.id} ... ")
        sys.stderr.flush()
        result = run_prompt(client, skill_content, prompt)
        sys.stderr.write(f"{result.status}\n")
        results.append(result)
        if i < len(prompts) - 1:
            time.sleep(SLEEP_BETWEEN_PROMPTS_S)

    # Results table.
    header = "| prompt_id | status | word_count | missing_patterns |"
    sep = "|-----------|--------|------------|------------------|"
    print(header)
    print(sep)
    for r in results:
        missing = ", ".join(r.missing_patterns) if r.missing_patterns else "-"
        if r.below_word_floor:
            missing = (
                f"(below min word count) {missing}"
                if r.missing_patterns
                else "(below min word count)"
            )
        print(
            f"| {r.prompt_id} | {r.status} | {r.word_count} | {missing} |"
        )

    return 0 if all(r.passed for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
