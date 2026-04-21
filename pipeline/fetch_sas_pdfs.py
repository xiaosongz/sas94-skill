"""Fetch SAS 9.4 docset PDFs and convert to markdown.

The earlier scraper (``fetch_sas_docs.py``) tried to walk
``documentation.sas.com`` HTML pages but those are React SPAs that
render client-side — the bare HTML shell is useless to markitdown.
The pivot this module implements: the same host also serves static
per-docset PDFs under a predictable URL pattern:

    https://documentation.sas.com/api/collections/pgmsascdc/<ver>/docsets/<name>/content/<name>.pdf?locale=en

where ``<ver>`` is a docset-CDC release such as ``9.4_3.4``. Those PDFs
are the static source of truth for the 9.4 doc tree, bypassing the SPA
entirely.

Pipeline:

    1. httpx.Client streams each PDF to pipeline/cache/docs/<name>.pdf.
       Before fetching, check ~/Downloads for a local copy (user may
       have pre-downloaded the two largest docsets — proc, lepg — to
       avoid hammering the server).
    2. Version-fallback: try ``9.4_3.4`` first, then ``9.4_3.5``, then
       ``v_001``. Only a 404 triggers the next attempt; other errors
       bubble out via the retry loop.
    3. markitdown (Python API) converts PDF -> markdown, cached as
       ``<name>.md`` next to the PDF.
    4. A sorted, key-sorted JSON manifest is written to
       pipeline/cache/extracted/sas_pdfs_manifest.json — each entry
       records the SHA256 of the PDF bytes, the source (network vs.
       local_copy), the final URL that worked, and word/page counts.

Rate limit: 1 req/sec with exponential backoff on 5xx. Rate limit
applies to network fetches only — local-copy reuse and cache hits do
not count. User-Agent identifies the skill version and repo.

Run from the pipeline directory (auto-discovers repo root via _common):

    cd pipeline && uv run python fetch_sas_pdfs.py

Re-runs are idempotent:
  - cached PDFs / markdown files are reused (no re-download, no
    re-convert). SHA256 is recomputed from the on-disk PDF each run, so
    a cache-hit run still produces the same manifest value.
  - The JSON manifest is sorted by docset name and dumped with
    sort_keys=True, so byte-identical output across re-runs.

Exit codes:
    0 - >= 5 docsets succeeded (min-viable set)
    1 - < 5 docsets succeeded (caller should escalate)
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import shutil
import sys
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Literal

import httpx
from pydantic import BaseModel

from _common import REPO_ROOT

# --- Paths ------------------------------------------------------------------

PIPELINE_DIR = REPO_ROOT / "pipeline"
CACHE_DIR = PIPELINE_DIR / "cache" / "docs"
EXTRACTED_DIR = PIPELINE_DIR / "cache" / "extracted"
OUT_FILE = EXTRACTED_DIR / "sas_pdfs_manifest.json"

DOWNLOADS_DIR = Path.home() / "Downloads"

# --- Net / UA ---------------------------------------------------------------

USER_AGENT = "sas94-skill/0.0.1 (+https://github.com/xiaosongz/sas94-skill)"
REQUEST_TIMEOUT = 60.0
RATE_LIMIT_SECONDS = 1.0
MAX_RETRIES = 4
BACKOFF_BASE = 2.0

# markitdown converts via pdfminer.six in-memory — feeding it the full
# 638 MB statug.pdf eats 30+ GB of RAM with no end in sight. Cap the
# PDFs we'll attempt to convert so a pathologically large docset cannot
# wedge the run. Anything above this is recorded as convert_error with
# a clear message and the PDF is still cached (SHA256 captured) so
# downstream tooling can pick it up manually.
MAX_PDF_CONVERT_MB = 200

# --- Minimum success bar ----------------------------------------------------

MIN_SUCCESSFUL_DOCSETS = 5

# --- Docset manifest --------------------------------------------------------

URL_TEMPLATE = (
    "https://documentation.sas.com/api/collections/pgmsascdc/"
    "{version}/docsets/{name}/content/{name}.pdf?locale=en"
)

# Version fallback order. If 9.4_3.4 404s we retry the same docset on
# 9.4_3.5 and then v_001. Only 404 triggers fallback — transient errors
# are handled by the per-URL retry loop inside _fetch_pdf.
VERSION_FALLBACKS: tuple[str, ...] = ("9.4_3.4", "9.4_3.5", "v_001")

# Ordered by task-spec order; sorted by docset name for the output
# manifest in run(). The list here is the fetch order.
DOCSETS: tuple[str, ...] = (
    "mcrolref",
    "lestmtsref",
    "lefunctionsref",
    "leforinforref",
    "odsug",
    "statug",
    "proc",
    "lepg",
)

# Local-copy detection: if ~/Downloads/<name>.pdf exists and is non-
# empty, copy it to the cache rather than downloading. Applies to the
# two largest docsets (proc ~20MB, lepg ~8MB) that the user pre-downloaded.
LOCAL_COPY_CANDIDATES: frozenset[str] = frozenset({"proc", "lepg"})


# --- Output schema ----------------------------------------------------------


class DocsetEntry(BaseModel):
    name: str
    url: str
    source: Literal["network", "local_copy"]
    pdf_path: str
    md_path: str | None
    source_sha256: str
    page_count: int | None = None
    word_count: int | None = None
    status: Literal["ok", "http_error", "convert_error"]
    http_status: int | None = None
    error: str | None = None


class SasPdfsOutput(BaseModel):
    source: str = (
        "documentation.sas.com pgmsascdc/9.4_3.4 PDFs "
        "(with fallback tries) + local Downloads"
    )
    scraped_at: str  # YYYY-MM-DD
    docsets: list[DocsetEntry]
    errors: list[str]


# --- Logging ----------------------------------------------------------------

log = logging.getLogger("fetch_sas_pdfs")


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        stream=sys.stderr,
    )


# --- Helpers ----------------------------------------------------------------


def _sha256_file(path: Path) -> str:
    """Stream a file through SHA256 and return the hex digest."""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


_WORD_RE = re.compile(r"\b[\w'-]+\b", re.UNICODE)


def _word_count(text: str) -> int:
    return len(_WORD_RE.findall(text))


# --- Fetch logic ------------------------------------------------------------


@dataclass
class FetchResult:
    ok: bool
    source: Literal["network", "local_copy"] | None
    url: str | None
    http_status: int | None
    error: str | None
    did_network: bool  # True if we hit the network (for rate-limit gating)


def _try_local_copy(name: str, dest: Path) -> bool:
    """Copy ~/Downloads/<name>.pdf into cache if present and non-empty."""
    if name not in LOCAL_COPY_CANDIDATES:
        return False
    src = DOWNLOADS_DIR / f"{name}.pdf"
    if not src.exists() or src.stat().st_size == 0:
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    log.info(
        "local copy: %s -> %s (%d bytes)",
        src,
        dest.name,
        dest.stat().st_size,
    )
    return True


def _fetch_one_url(
    client: httpx.Client, url: str, dest: Path
) -> tuple[bool, int | None, str | None]:
    """GET one URL with retry/backoff. Returns (ok, http_status, error).

    Transient HTTP errors (429, 5xx) retry with exponential backoff.
    A clean 404 returns (False, 404, ...) so the caller can attempt the
    next version in the fallback list. Any other 4xx is terminal.
    """
    attempt = 0
    while attempt < MAX_RETRIES:
        attempt += 1
        try:
            with client.stream("GET", url) as resp:
                if resp.status_code == 200:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    with dest.open("wb") as fh:
                        for chunk in resp.iter_bytes(chunk_size=64 * 1024):
                            fh.write(chunk)
                    size = dest.stat().st_size
                    log.info("fetched %s (%d bytes) from %s", dest.name, size, url)
                    return True, 200, None
                if resp.status_code == 404:
                    log.info("http 404 on %s", url)
                    return False, 404, "HTTP 404"
                if resp.status_code in (429, 500, 502, 503, 504):
                    backoff = BACKOFF_BASE**attempt
                    log.warning(
                        "transient %s on %s; backoff %.1fs (attempt %d/%d)",
                        resp.status_code,
                        url,
                        backoff,
                        attempt,
                        MAX_RETRIES,
                    )
                    time.sleep(backoff)
                    continue
                log.warning("http %s on %s; giving up", resp.status_code, url)
                return False, resp.status_code, f"HTTP {resp.status_code}"
        except httpx.HTTPError as exc:
            backoff = BACKOFF_BASE**attempt
            log.warning(
                "httpx error %s on %s; backoff %.1fs (attempt %d/%d)",
                exc,
                url,
                backoff,
                attempt,
                MAX_RETRIES,
            )
            time.sleep(backoff)
    return False, None, f"exhausted {MAX_RETRIES} retries"


def _fetch_pdf(
    client: httpx.Client,
    name: str,
    dest: Path,
    *,
    first_fetch_this_run: bool,
) -> FetchResult:
    """Acquire PDF for docset `name` into `dest`.

    Resolution order:
      1. Cache-hit: if dest already exists non-empty, reuse. No network.
      2. Local-copy: if ~/Downloads/<name>.pdf exists, copy. No network.
      3. Network: iterate VERSION_FALLBACKS, 404 -> next version.
    """
    if dest.exists() and dest.stat().st_size > 0:
        # Cache hit. We can't tell after-the-fact whether the original
        # acquisition was network or local_copy, so we default to
        # reporting the cached entry as "network" UNLESS the user still
        # has a matching ~/Downloads file AND the sha matches — we
        # conservatively just keep "network" (the prior manifest carries
        # the ground truth for a sophisticated diff). Simpler: re-detect
        # via Downloads presence to stay consistent across re-runs.
        if name in LOCAL_COPY_CANDIDATES:
            src = DOWNLOADS_DIR / f"{name}.pdf"
            if src.exists() and src.stat().st_size > 0:
                # Keep label stable: this docset is served by local copy.
                log.info("cache hit pdf (local_copy): %s", dest.name)
                return FetchResult(
                    ok=True,
                    source="local_copy",
                    url=str(src),
                    http_status=None,
                    error=None,
                    did_network=False,
                )
        log.info("cache hit pdf: %s", dest.name)
        # The version/URL recorded for this cached PDF: we pick the
        # first fallback we'd try. This only matters if the Downloads
        # copy is gone AND the cache is a network one — idempotency is
        # preserved because dest + sha stay identical.
        return FetchResult(
            ok=True,
            source="network",
            url=URL_TEMPLATE.format(version=VERSION_FALLBACKS[0], name=name),
            http_status=200,
            error=None,
            did_network=False,
        )

    # Try local copy first (cheap, no network).
    if _try_local_copy(name, dest):
        return FetchResult(
            ok=True,
            source="local_copy",
            url=str(DOWNLOADS_DIR / f"{name}.pdf"),
            http_status=None,
            error=None,
            did_network=False,
        )

    # Network: walk the version fallback list.
    last_status: int | None = None
    last_error: str | None = None
    for idx, version in enumerate(VERSION_FALLBACKS):
        url = URL_TEMPLATE.format(version=version, name=name)

        # Rate limit between network calls. We're about to hit the
        # network — respect 1 req/sec except for the very first fetch
        # of the entire run.
        if not first_fetch_this_run or idx > 0:
            time.sleep(RATE_LIMIT_SECONDS)

        ok, status, err = _fetch_one_url(client, url, dest)
        if ok:
            return FetchResult(
                ok=True,
                source="network",
                url=url,
                http_status=status or 200,
                error=None,
                did_network=True,
            )
        last_status = status
        last_error = err
        if status == 404:
            log.info("version %s 404 for %s; trying next", version, name)
            continue
        # Non-404 terminal error: don't keep trying other versions.
        return FetchResult(
            ok=False,
            source=None,
            url=url,
            http_status=status,
            error=err,
            did_network=True,
        )

    # All versions exhausted.
    return FetchResult(
        ok=False,
        source=None,
        url=URL_TEMPLATE.format(version=VERSION_FALLBACKS[-1], name=name),
        http_status=last_status,
        error=f"all versions 404/failed: {last_error}",
        did_network=True,
    )


# --- Convert ----------------------------------------------------------------


def _convert_pdf(
    pdf_path: Path, md_path: Path
) -> tuple[bool, str | None, int | None]:
    """Convert PDF -> markdown via markitdown Python API. Returns (ok, err, page_count).

    page_count is extracted if markitdown surfaces it via a
    ``page_count`` / ``pages`` attribute on the result; otherwise None.
    """
    if md_path.exists() and md_path.stat().st_size > 0:
        log.info("cache hit md:  %s", md_path.name)
        return True, None, None

    pdf_mb = pdf_path.stat().st_size / (1024 * 1024)
    if pdf_mb > MAX_PDF_CONVERT_MB:
        msg = (
            f"pdf {pdf_mb:.0f} MB exceeds markitdown convert cap "
            f"{MAX_PDF_CONVERT_MB} MB (pdfminer OOMs)"
        )
        log.warning("skip convert %s: %s", pdf_path.name, msg)
        return False, msg, None

    try:
        from markitdown import MarkItDown

        md = MarkItDown()
        result = md.convert(str(pdf_path))
        text = result.text_content or ""
        if not text.strip():
            return False, "empty markdown output", None
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(text, encoding="utf-8")
        log.info(
            "converted %s -> %s (%d chars)",
            pdf_path.name,
            md_path.name,
            len(text),
        )
        # Surface page_count if the markitdown result exposes one.
        page_count: int | None = None
        for attr in ("page_count", "pages", "num_pages"):
            val = getattr(result, attr, None)
            if isinstance(val, int) and val > 0:
                page_count = val
                break
        return True, None, page_count
    except Exception as exc:  # noqa: BLE001 - markitdown raises bare Exception
        log.exception("markitdown failed on %s: %s", pdf_path.name, exc)
        return False, f"markitdown: {exc}", None


# --- Orchestration ----------------------------------------------------------


def run() -> int:
    _configure_logging()

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/pdf,*/*;q=0.9",
    }
    entries: list[DocsetEntry] = []
    errors: list[str] = []
    network_fetches_done = 0

    with httpx.Client(
        headers=headers,
        timeout=REQUEST_TIMEOUT,
        follow_redirects=True,
        http2=True,
    ) as client:
        for name in DOCSETS:
            pdf_path = CACHE_DIR / f"{name}.pdf"
            md_path = CACHE_DIR / f"{name}.md"

            fetch = _fetch_pdf(
                client,
                name,
                pdf_path,
                first_fetch_this_run=(network_fetches_done == 0),
            )
            if fetch.did_network:
                network_fetches_done += 1

            if not fetch.ok:
                entries.append(
                    DocsetEntry(
                        name=name,
                        url=fetch.url or "",
                        source="network",
                        pdf_path="",
                        md_path=None,
                        source_sha256="",
                        status="http_error",
                        http_status=fetch.http_status,
                        error=fetch.error,
                    )
                )
                errors.append(f"{name}: fetch failed: {fetch.error}")
                continue

            sha = _sha256_file(pdf_path)

            conv_ok, conv_err, page_count = _convert_pdf(pdf_path, md_path)

            assert fetch.source is not None  # narrowing for type-checkers
            if not conv_ok:
                entries.append(
                    DocsetEntry(
                        name=name,
                        url=fetch.url or "",
                        source=fetch.source,
                        pdf_path=str(pdf_path.relative_to(REPO_ROOT)),
                        md_path=None,
                        source_sha256=sha,
                        status="convert_error",
                        http_status=fetch.http_status,
                        error=conv_err,
                    )
                )
                errors.append(f"{name}: convert failed: {conv_err}")
                continue

            text = md_path.read_text(encoding="utf-8")
            entries.append(
                DocsetEntry(
                    name=name,
                    url=fetch.url or "",
                    source=fetch.source,
                    pdf_path=str(pdf_path.relative_to(REPO_ROOT)),
                    md_path=str(md_path.relative_to(REPO_ROOT)),
                    source_sha256=sha,
                    page_count=page_count,
                    word_count=_word_count(text),
                    status="ok",
                    http_status=fetch.http_status,
                )
            )

    # Deterministic ordering: by docset name.
    entries.sort(key=lambda e: e.name)
    errors.sort()

    out = SasPdfsOutput(
        scraped_at=date.today().isoformat(),
        docsets=entries,
        errors=errors,
    )

    # Pydantic validation round-trip.
    validated = SasPdfsOutput.model_validate(out.model_dump())

    OUT_FILE.write_text(
        json.dumps(validated.model_dump(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    ok_count = sum(1 for e in entries if e.status == "ok")
    log.info(
        "wrote %s (%d/%d docsets ok, %d errors)",
        OUT_FILE,
        ok_count,
        len(entries),
        len(errors),
    )
    for e in entries:
        log.info(
            "  [%s] %-15s source=%-10s sha=%s",
            e.status,
            e.name,
            e.source,
            (e.source_sha256 or "-")[:12],
        )

    if ok_count < MIN_SUCCESSFUL_DOCSETS:
        log.error(
            "only %d/%d docsets succeeded (min %d); escalate to controller",
            ok_count,
            len(entries),
            MIN_SUCCESSFUL_DOCSETS,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(run())
