"""Fetch SUGI / PharmaSUG / SAS Global Forum PDFs and convert to markdown.

Targets three topic clusters identified in the Phase 1 source tier table:

  - Paul Dorfman on the data-step hash object
  - Kirk Paul Lafler on PROC SQL
  - Macro quoting (Ian Whitlock, Art Carpenter, Harry Droogendyk, etc.)

Discovery is *not* attempted: lexjansen index pages are brittle and scraping
them is out of scope for Phase 1. Instead a hardcoded seed list of 5-8
specific paper URLs is iterated. Some URLs will 404 over time (SAS Global
Forum in particular rotates proceeding paths) — the script records a
per-URL status and keeps going. It only fails loud if < 5 papers survive.

Pipeline:

    1. httpx.Client streams each PDF to pipeline/cache/lexjansen/<slug>.pdf
    2. markitdown (Python API) converts PDF -> markdown, cached alongside
    3. A sorted, key-sorted JSON manifest is written to
       pipeline/cache/extracted/lexjansen.json

Downstream (T13 hash-tables.md, T16 idioms-from-lexjansen.md) reads the
markdown files directly and enforces the < 90 verbatim words per paper rule
spelled out in spec Sec. Risks. This script never embeds extracted content
in the manifest beyond a 500-char quick-review snippet.

Rate limit: 1 req/sec with exponential backoff on 5xx. User-Agent identifies
the skill version and repo per SUGI archive etiquette.

Run from the pipeline directory (auto-discovers repo root via _common):

    cd pipeline && uv run python fetch_lexjansen.py

Re-runs are idempotent:
  - cached PDFs / markdown files are reused (no re-download, no re-convert)
  - the JSON manifest is sorted by (topic_cluster, title) and dumped with
    sort_keys=True, so byte-identical output across re-runs

Exit codes:
    0 - >= 5 papers succeeded
    1 - < 5 papers succeeded (caller should escalate)
"""

from __future__ import annotations

import json
import logging
import re
import sys
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import httpx
from pydantic import BaseModel, Field

from _common import REPO_ROOT

# --- Paths ------------------------------------------------------------------

PIPELINE_DIR = REPO_ROOT / "pipeline"
CACHE_DIR = PIPELINE_DIR / "cache" / "lexjansen"
EXTRACTED_DIR = PIPELINE_DIR / "cache" / "extracted"
OUT_FILE = EXTRACTED_DIR / "lexjansen.json"

# --- Net / UA ---------------------------------------------------------------

USER_AGENT = "sas94-skill/0.0.1 (+https://github.com/xiaosongz/sas94-skill)"
REQUEST_TIMEOUT = 60.0
RATE_LIMIT_SECONDS = 1.0
MAX_RETRIES = 4
BACKOFF_BASE = 2.0

# --- Minimum success bar ----------------------------------------------------

MIN_SUCCESSFUL_PAPERS = 5


# --- Seed list --------------------------------------------------------------


@dataclass(frozen=True)
class SeedPaper:
    """A targeted SUGI / PharmaSUG / SGF paper URL + metadata."""

    title: str
    author: str
    conference: str
    url: str
    topic_cluster: str  # "hash-tables" | "proc-sql" | "macro-quoting"
    slug: str  # stable filename stem, used for both <slug>.pdf and <slug>.md


SEEDS: tuple[SeedPaper, ...] = (
    # --- Paul Dorfman - hash tables -----------------------------------------
    # The original PharmaSUG 2008 / PhUSE 2006 Dorfman URLs in the spec 404 on
    # lexjansen (confirmed 2026-04-21). Replaced with confirmed-working peers
    # from the same author on the same topic, discovered via a targeted
    # site:lexjansen.com search.
    SeedPaper(
        title="Hash Crash and Beyond",
        author="Paul M. Dorfman",
        conference="NESUG 2007",
        url="https://www.lexjansen.com/nesug/nesug07/ff/ff03.pdf",
        topic_cluster="hash-tables",
        slug="dorfman-2007-nesug-hash-crash",
    ),
    SeedPaper(
        title="The DATA step Hash Object as a Programming Tool",
        author="Paul M. Dorfman",
        conference="SUGI 30 (2005)",
        url="https://support.sas.com/resources/papers/proceedings/proceedings/sugi30/236-30.pdf",
        topic_cluster="hash-tables",
        slug="dorfman-2005-sugi30-hash-tool",
    ),
    SeedPaper(
        title="Using the SAS Hash Object with Duplicate Key Entries",
        author="Paul M. Dorfman",
        conference="SESUG 2015",
        url="https://www.lexjansen.com/sesug/2015/94_Final_PDF.pdf",
        topic_cluster="hash-tables",
        slug="dorfman-2015-sesug-hash-duplicate-keys",
    ),
    # --- Kirk Paul Lafler - PROC SQL ----------------------------------------
    # The WUSS 2016 Lafler URL in the spec 404s; replaced with two confirmed-
    # working Lafler papers on PROC SQL topics.
    SeedPaper(
        title="Conditional Processing Using the Case Expression in PROC SQL",
        author="Kirk Paul Lafler",
        conference="WUSS 2011",
        url="https://www.lexjansen.com/wuss/2011/coders/Papers_Lafler_K_72492.pdf",
        topic_cluster="proc-sql",
        slug="lafler-2011-wuss-procsql-case",
    ),
    SeedPaper(
        title="Best Tips and Techniques Using PROC SQL",
        author="Kirk Paul Lafler",
        conference="SAS Global Forum 2011",
        url="https://support.sas.com/resources/papers/proceedings11/101-2011.pdf",
        topic_cluster="proc-sql",
        slug="lafler-2011-sgf-procsql-tips",
    ),
    SeedPaper(
        title="Essential PROC SQL Join Techniques Using SAS",
        author="Kirk Paul Lafler",
        conference="MWSUG 2015",
        url="https://www.lexjansen.com/mwsug/2015/RF/MWSUG-2015-RF-02.pdf",
        topic_cluster="proc-sql",
        slug="lafler-2015-mwsug-procsql-joins",
    ),
    # --- Macro quoting ------------------------------------------------------
    # The PharmaSUG 2015 Droogendyk URL in the spec 404s; replaced with two
    # confirmed-working macro-quoting papers (Whitlock canonical treatment +
    # modern PhUSE 2019 deep-dive).
    SeedPaper(
        # NB: the spec referenced SUGI 29 paper 243-29 for Whitlock, but that
        # paper is actually Slaughter & Delwiche "SAS Macro Programming for
        # Beginners" — a different paper. The real Whitlock "A Serious Look at
        # Macro Quoting" lives on NESUG 2009 (and a revised 2010 version).
        title="A Serious Look at Macro Quoting",
        author="Ian Whitlock",
        conference="NESUG 2009",
        url="https://www.lexjansen.com/nesug/nesug09/bb/BB02.pdf",
        topic_cluster="macro-quoting",
        slug="whitlock-2009-nesug-macro-quoting",
    ),
    SeedPaper(
        title="SAS Macro Quoting - A Look Behind the Scenes",
        author="PhUSE contributor",
        conference="PhUSE 2019",
        url="https://www.lexjansen.com/phuse/2019/sm/SM04.pdf",
        topic_cluster="macro-quoting",
        slug="phuse-2019-macro-quoting-behind-scenes",
    ),
)


# --- Output schema ----------------------------------------------------------


class PaperEntry(BaseModel):
    title: str
    author: str
    conference: str
    url: str
    topic_cluster: str
    status: str  # "ok" | "http_error" | "convert_error"
    http_status: int | None = None
    markdown_path: str | None = None
    pdf_path: str | None = None
    word_count: int | None = None
    extract_summary: str | None = Field(
        default=None,
        description="First ~500 chars of extracted markdown, for quick review only.",
    )
    error: str | None = None


class LexjansenOutput(BaseModel):
    source: str = "lexjansen.com + support.sas.com proceedings"
    scraped_at: str  # YYYY-MM-DD
    papers: list[PaperEntry]
    errors: list[str]


# --- Logging ----------------------------------------------------------------

log = logging.getLogger("fetch_lexjansen")


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        stream=sys.stderr,
    )


# --- Fetch ------------------------------------------------------------------


def _fetch_pdf(client: httpx.Client, seed: SeedPaper, dest: Path) -> tuple[bool, int | None, str | None]:
    """Download a PDF with rate limit + exponential backoff.

    Returns (ok, http_status, error_message).
    """
    if dest.exists() and dest.stat().st_size > 0:
        log.info("cache hit pdf: %s", dest.name)
        return True, None, None

    attempt = 0
    while attempt < MAX_RETRIES:
        attempt += 1
        try:
            with client.stream("GET", seed.url) as resp:
                if resp.status_code == 200:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    with dest.open("wb") as fh:
                        for chunk in resp.iter_bytes(chunk_size=64 * 1024):
                            fh.write(chunk)
                    size = dest.stat().st_size
                    log.info(
                        "fetched %s (%d bytes) from %s", dest.name, size, seed.url
                    )
                    return True, 200, None
                if resp.status_code in (429, 500, 502, 503, 504):
                    backoff = BACKOFF_BASE ** attempt
                    log.warning(
                        "transient %s on %s; backoff %.1fs (attempt %d/%d)",
                        resp.status_code,
                        seed.url,
                        backoff,
                        attempt,
                        MAX_RETRIES,
                    )
                    time.sleep(backoff)
                    continue
                # 4xx other than 429 = permanent
                log.warning(
                    "http %s on %s; giving up", resp.status_code, seed.url
                )
                return False, resp.status_code, f"HTTP {resp.status_code}"
        except httpx.HTTPError as exc:
            backoff = BACKOFF_BASE ** attempt
            log.warning(
                "httpx error %s on %s; backoff %.1fs (attempt %d/%d)",
                exc,
                seed.url,
                backoff,
                attempt,
                MAX_RETRIES,
            )
            time.sleep(backoff)
    return False, None, f"exhausted {MAX_RETRIES} retries"


# --- Convert ----------------------------------------------------------------


def _convert_pdf(pdf_path: Path, md_path: Path) -> tuple[bool, str | None]:
    """Convert PDF -> markdown via markitdown Python API, cache output."""
    if md_path.exists() and md_path.stat().st_size > 0:
        log.info("cache hit md:  %s", md_path.name)
        return True, None
    try:
        # Import locally so the script can still start up and record HTTP
        # failures even if markitdown's heavy transitive deps (onnxruntime,
        # magika) mis-load on an exotic platform.
        from markitdown import MarkItDown

        md = MarkItDown()
        result = md.convert(str(pdf_path))
        text = result.text_content or ""
        if not text.strip():
            return False, "empty markdown output"
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(text, encoding="utf-8")
        log.info(
            "converted %s -> %s (%d chars)", pdf_path.name, md_path.name, len(text)
        )
        return True, None
    except Exception as exc:  # noqa: BLE001 - markitdown raises bare Exception
        log.exception("markitdown failed on %s: %s", pdf_path.name, exc)
        return False, f"markitdown: {exc}"


# --- Word count + summary ---------------------------------------------------

_WORD_RE = re.compile(r"\b[\w'-]+\b", re.UNICODE)


def _word_count(text: str) -> int:
    return len(_WORD_RE.findall(text))


def _summary(text: str, limit: int = 500) -> str:
    # Collapse whitespace so the snippet is one readable paragraph in the JSON
    collapsed = re.sub(r"\s+", " ", text).strip()
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[:limit].rstrip() + "..."


# --- Orchestration ----------------------------------------------------------


def run() -> int:
    _configure_logging()

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)

    headers = {"User-Agent": USER_AGENT, "Accept": "application/pdf,*/*;q=0.9"}
    entries: list[PaperEntry] = []
    errors: list[str] = []

    with httpx.Client(
        headers=headers,
        timeout=REQUEST_TIMEOUT,
        follow_redirects=True,
        http2=True,
    ) as client:
        for i, seed in enumerate(SEEDS):
            # Rate limit between requests (skipped for first request and
            # cache-hit downloads — cache-hit is effectively instant but
            # the 1 req/sec applies to network traffic only).
            if i > 0:
                time.sleep(RATE_LIMIT_SECONDS)

            pdf_path = CACHE_DIR / f"{seed.slug}.pdf"
            md_path = CACHE_DIR / f"{seed.slug}.md"

            ok, http_status, err = _fetch_pdf(client, seed, pdf_path)
            if not ok:
                entries.append(
                    PaperEntry(
                        title=seed.title,
                        author=seed.author,
                        conference=seed.conference,
                        url=seed.url,
                        topic_cluster=seed.topic_cluster,
                        status="http_error",
                        http_status=http_status,
                        error=err,
                    )
                )
                errors.append(f"{seed.slug}: fetch failed: {err}")
                continue

            conv_ok, conv_err = _convert_pdf(pdf_path, md_path)
            if not conv_ok:
                entries.append(
                    PaperEntry(
                        title=seed.title,
                        author=seed.author,
                        conference=seed.conference,
                        url=seed.url,
                        topic_cluster=seed.topic_cluster,
                        status="convert_error",
                        http_status=http_status or 200,
                        pdf_path=str(pdf_path.relative_to(REPO_ROOT)),
                        error=conv_err,
                    )
                )
                errors.append(f"{seed.slug}: convert failed: {conv_err}")
                continue

            text = md_path.read_text(encoding="utf-8")
            entries.append(
                PaperEntry(
                    title=seed.title,
                    author=seed.author,
                    conference=seed.conference,
                    url=seed.url,
                    topic_cluster=seed.topic_cluster,
                    status="ok",
                    http_status=http_status or 200,
                    pdf_path=str(pdf_path.relative_to(REPO_ROOT)),
                    markdown_path=str(md_path.relative_to(REPO_ROOT)),
                    word_count=_word_count(text),
                    extract_summary=_summary(text),
                )
            )

    # Deterministic sort: cluster first, then title
    entries.sort(key=lambda e: (e.topic_cluster, e.title))
    errors.sort()

    out = LexjansenOutput(
        scraped_at=date.today().isoformat(),
        papers=entries,
        errors=errors,
    )

    # Pydantic validation (will raise on malformed dict)
    validated = LexjansenOutput.model_validate(out.model_dump())

    OUT_FILE.write_text(
        json.dumps(validated.model_dump(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    ok_count = sum(1 for e in entries if e.status == "ok")
    log.info(
        "wrote %s (%d/%d papers ok, %d errors)",
        OUT_FILE,
        ok_count,
        len(entries),
        len(errors),
    )
    for e in entries:
        log.info("  [%s] %-18s %s", e.status, e.topic_cluster, e.title[:60])

    if ok_count < MIN_SUCCESSFUL_PAPERS:
        log.error(
            "only %d/%d papers succeeded (min %d); escalate to controller",
            ok_count,
            len(entries),
            MIN_SUCCESSFUL_PAPERS,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(run())
