"""Validate that every upstream `Source:` URL in `references/*.md` and
`docs/rule-provenance.md` still resolves (no 404s, no DNS failures).

Called by `.github/workflows/validate-sources.yml` on a weekly schedule
and on PRs that touch reference content.

Strategy:
- Walk `references/*.md` → extract every `Source: https?://...` line.
- Walk `docs/rule-provenance.md` → extract every `https?://...` URL from
  the Source column of the markdown table.
- Deduplicate (one provenance row per rule + the same URL appears in the
  reference file = two hits for the same URL).
- Issue `httpx.head(..., follow_redirects=True)` with a 10s timeout,
  max 5 concurrent requests, 200ms delay between batches.
- Treat any 4xx other than 403 as failure. GitHub's `raw.githubusercontent.com`
  and some CDN-fronted docs return 403 for bot-shaped User-Agents on HEAD;
  mark those as pass with a note rather than failing the run.
- Exit 1 if any real failure; exit 0 otherwise. Print a summary table.

Needs `httpx` (pipeline dep) and stdlib asyncio.
"""

from __future__ import annotations

import asyncio
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import httpx

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
REFERENCES_DIR = REPO_ROOT / "plugins" / "sas94" / "skills" / "sas94" / "references"
PROVENANCE_MD = REPO_ROOT / "docs" / "rule-provenance.md"

# Capture the URL after `Source:` in reference files. The URL runs until
# whitespace or end of line; trailing commentary like " — hand-transcribed"
# is not part of the URL.
SOURCE_LINE_RE = re.compile(r"^Source:\s+(https?://\S+)", re.MULTILINE)

# Capture any http(s) URL appearing inside the provenance table. We do not
# try to parse the table structure — a raw regex over the text is enough
# because URLs never appear in any other column.
URL_RE = re.compile(r"https?://[^\s)<>|]+")

MAX_CONCURRENCY = 5
BATCH_DELAY_S = 0.2
REQUEST_TIMEOUT_S = 10.0


@dataclass
class Result:
    url: str
    status: int | None  # None → network error
    note: str
    latency_ms: float


def collect_urls() -> list[str]:
    urls: set[str] = set()

    for ref in sorted(REFERENCES_DIR.glob("*.md")):
        for m in SOURCE_LINE_RE.finditer(ref.read_text(encoding="utf-8")):
            urls.add(m.group(1).rstrip(".,;)"))

    if PROVENANCE_MD.exists():
        for m in URL_RE.finditer(PROVENANCE_MD.read_text(encoding="utf-8")):
            urls.add(m.group(0).rstrip(".,;)"))

    return sorted(urls)


async def check_one(
    client: httpx.AsyncClient, url: str, sem: asyncio.Semaphore
) -> Result:
    async with sem:
        loop = asyncio.get_event_loop()
        t0 = loop.time()
        try:
            resp = await client.head(url, follow_redirects=True, timeout=REQUEST_TIMEOUT_S)
            latency = (loop.time() - t0) * 1000
            status = resp.status_code
            if status == 403:
                note = "403 — accepted (bot-UA quirk)"
            elif status >= 400:
                note = f"FAIL ({status})"
            elif status >= 300:
                note = f"redirect ({status})"
            else:
                note = "ok"
            return Result(url=url, status=status, note=note, latency_ms=latency)
        except httpx.HTTPError as exc:
            latency = (loop.time() - t0) * 1000
            return Result(
                url=url,
                status=None,
                note=f"FAIL (network: {type(exc).__name__}: {exc})",
                latency_ms=latency,
            )


async def run(urls: list[str]) -> list[Result]:
    sem = asyncio.Semaphore(MAX_CONCURRENCY)
    # A realistic UA cuts the 403-from-bot-UA rate on CDN-fronted docs.
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; sas94-skill-link-check/0.1; "
            "+https://github.com/sas94-skill)"
        )
    }
    async with httpx.AsyncClient(headers=headers, http2=True) as client:
        results: list[Result] = []
        # Batches of MAX_CONCURRENCY with a small delay between batches so
        # we don't pummel github.com / sas.com.
        for i in range(0, len(urls), MAX_CONCURRENCY):
            batch = urls[i : i + MAX_CONCURRENCY]
            batch_results = await asyncio.gather(
                *(check_one(client, u, sem) for u in batch)
            )
            results.extend(batch_results)
            if i + MAX_CONCURRENCY < len(urls):
                await asyncio.sleep(BATCH_DELAY_S)
        return results


def is_failure(r: Result) -> bool:
    if r.status is None:
        return True
    if r.status == 403:
        return False
    return r.status >= 400


def render_summary(results: list[Result]) -> str:
    """Build a GH-Actions-friendly summary table."""
    lines = [
        "| Status | Latency (ms) | URL | Note |",
        "|--------|-------------:|-----|------|",
    ]
    for r in sorted(results, key=lambda r: (is_failure(r), r.url)):
        status_cell = str(r.status) if r.status is not None else "ERR"
        lines.append(
            f"| {status_cell} | {r.latency_ms:.0f} | {r.url} | {r.note} |"
        )
    return "\n".join(lines)


def main() -> int:
    urls = collect_urls()
    if not urls:
        print("No URLs found in references/ or docs/rule-provenance.md.")
        return 0

    print(f"Checking {len(urls)} unique upstream URL(s)...", file=sys.stderr)
    results = asyncio.run(run(urls))

    print(render_summary(results))

    failures = [r for r in results if is_failure(r)]
    if failures:
        print(
            f"\nvalidate-sources: {len(failures)} URL(s) failed.",
            file=sys.stderr,
        )
        for r in failures:
            print(f"  FAIL {r.status} {r.url}  ({r.note})", file=sys.stderr)
        return 1

    print(f"\nvalidate-sources: all {len(results)} URL(s) ok.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
