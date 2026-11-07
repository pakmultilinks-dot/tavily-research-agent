"""Tavily Extract API client. Verified parameters only.

Verified 2026-11-07 from the official docs, endpoint page
https://docs.tavily.com/documentation/api-reference/endpoint/extract
(page updated 2026-09-15):
- Endpoint: POST https://api.tavily.com/extract
- Auth header: Authorization: Bearer <TAVILY_API_KEY>
- Body: urls (required, one URL or a list, up to 20 per request),
  query (optional, reranks chunks), chunks_per_source (1 to 5,
  default 3, only when query is provided), extract_depth basic
  (default) or advanced, format markdown (default) or text,
  timeout 1.0 to 60.0 seconds (defaults 10 basic, 30 advanced),
  include_images and include_favicon default false.
- Response: results (extracted content), failed_results (URLs
  that could not be processed), response_time, usage, request_id.
  Check BOTH results and failed_results even on HTTP 200.
- Cost, from the same docs: basic 1 credit per 5 successful URL
  extractions, advanced 2 credits per 5. Enriching the 37 kept
  URLs at basic depth, all successful, is 37 / 5 rounded up,
  8 credits. That is arithmetic from the documented per-5 cost,
  not a measured bill.
- Extract does NOT return published_date. The date from the
  search result is kept and is never overwritten here.

Unverified: exact field names inside each results entry beyond
url, raw_content, images, and favicon. This client reads url
and raw_content, and treats anything else as optional.

The key is read ONLY from the TAVILY_API_KEY environment
variable, through tavily_agent.tavily_client.get_api_key. It is
never hardcoded and never written to any file by this code.
On HTTP 401 it raises TavilyAuthError with the fix message,
and the caller keeps the search snippet as fallback.
"""
from __future__ import annotations

import re

import requests

from .tavily_client import (
    AUTH_FIX_MESSAGE,
    TavilyAuthError,
    get_api_key,
    key_format_warning,
)

EXTRACT_URL = "https://api.tavily.com/extract"
MAX_URLS_PER_REQUEST = 20
DEFAULT_CHUNKS_PER_SOURCE = 3
MAX_CHUNKS_PER_SOURCE = 5
DEFAULT_TIMEOUT_SECONDS = 30
MAX_ATTEMPTS = 2  # one first try plus one retry, on timeout only, never on 401
CHUNK_CHARS = 800  # docs: chunks are short snippets, about 800 characters each


def _first_chunk(raw_content: str) -> str:
    """Return the first extracted chunk of a raw_content string.

    When the content carries explicit chunk markers, cut before
    the second chunk. Otherwise take the first 800 characters,
    which matches the documented chunk size, and do not invent
    anything beyond the returned text.
    """
    text = (raw_content or "").strip()
    if not text:
        return ""
    match = re.search(r"chunk\s*2\b", text, flags=re.IGNORECASE)
    if match:
        text = text[: match.start()].strip()
    return text[:CHUNK_CHARS].strip()


def _entry_url(entry) -> str:
    if isinstance(entry, dict):
        return (entry.get("url") or "").strip()
    if isinstance(entry, str):
        return entry.strip()
    return ""


def extract_batch(urls: list[str], query: str | None = None,
                  extract_depth: str = "basic",
                  chunks_per_source: int = DEFAULT_CHUNKS_PER_SOURCE,
                  api_key: str | None = None,
                  timeout: int = DEFAULT_TIMEOUT_SECONDS) -> dict:
    """Extract content for up to 20 URLs in one request.

    Returns {"extracted": {url: first_chunk}, "failed": [url, ...]}.
    URLs are batched by the caller in groups of 20; this function
    sends exactly one request. On 401 it raises TavilyAuthError.
    On timeout it retries once, then raises RuntimeError.
    """
    if not urls:
        return {"extracted": {}, "failed": []}
    if len(urls) > MAX_URLS_PER_REQUEST:
        raise ValueError(
            f"Extract takes at most {MAX_URLS_PER_REQUEST} URLs per "
            f"request, got {len(urls)}. Split the list first."
        )
    if extract_depth not in ("basic", "advanced"):
        raise ValueError("extract_depth must be 'basic' or 'advanced'.")
    if chunks_per_source < 1 or chunks_per_source > MAX_CHUNKS_PER_SOURCE:
        raise ValueError(
            f"chunks_per_source must be 1 to {MAX_CHUNKS_PER_SOURCE}, "
            f"got {chunks_per_source}."
        )
    key = (api_key or "").strip() or get_api_key()
    payload: dict = {
        "urls": list(urls),
        "extract_depth": extract_depth,
        "format": "markdown",
    }
    if query:
        payload["query"] = query
        payload["chunks_per_source"] = chunks_per_source
    response = None
    last_timeout = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = requests.post(
                EXTRACT_URL,
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=timeout,
            )
            break
        except requests.Timeout as exc:
            last_timeout = exc
            if attempt == MAX_ATTEMPTS:
                raise RuntimeError(
                    "Tavily Extract timed out after one retry. "
                    "The request was sent twice and got no response. "
                    "The key was not logged and is not shown here."
                ) from exc
    if response is None:  # pragma: no cover - guarded by the loop above
        raise RuntimeError("Tavily Extract produced no response.") from last_timeout
    if response.status_code == 401:
        message = AUTH_FIX_MESSAGE
        warning = key_format_warning(key)
        if warning:
            message += " " + warning
        raise TavilyAuthError(message)
    response.raise_for_status()
    data = response.json() if isinstance(response.json(), dict) else {}
    extracted: dict[str, str] = {}
    for entry in data.get("results", []) or []:
        url = _entry_url(entry)
        if not url:
            continue
        chunk = _first_chunk(entry.get("raw_content", "") or "")
        if chunk:
            extracted[url] = chunk
    failed = []
    for entry in data.get("failed_results", []) or []:
        url = _entry_url(entry)
        if url and url not in extracted:
            failed.append(url)
    for url in urls:
        if url not in extracted and url not in failed:
            failed.append(url)
    return {"extracted": extracted, "failed": failed}


def extract_for_urls(urls: list[str], query: str | None = None,
                     extract_depth: str = "basic",
                     chunks_per_source: int = DEFAULT_CHUNKS_PER_SOURCE,
                     api_key: str | None = None) -> dict:
    """Extract content for any number of URLs, in batches of 20.

    Returns the same {"extracted": {...}, "failed": [...]} shape
    as extract_batch, merged across batches.
    """
    merged: dict[str, str] = {}
    failed: list[str] = []
    for start in range(0, len(urls), MAX_URLS_PER_REQUEST):
        batch = extract_batch(
            urls[start:start + MAX_URLS_PER_REQUEST],
            query=query, extract_depth=extract_depth,
            chunks_per_source=chunks_per_source, api_key=api_key,
        )
        merged.update(batch["extracted"])
        failed.extend(batch["failed"])
    return {"extracted": merged, "failed": failed}


def enrich_top_results(results, subject: str, top_n: int = 8,
                       api_key: str | None = None) -> dict:
    """Attach the first extracted chunk to the top N results.

    results are kept developments in briefing order (newest
    first). Only the first top_n are enriched, so the cost stays
    bounded. Each enriched result gains full_content; its title,
    URL, published date, and snippet are never changed. A result
    whose URL fails Extract keeps its snippet as fallback and is
    counted in failed. Returns {"enriched": n, "failed": n}.
    """
    top = list(results)[:top_n]
    if not top:
        return {"enriched": 0, "failed": 0}
    urls = [r.url for r in top if r.url]
    if not urls:
        return {"enriched": 0, "failed": 0}
    query = f"{subject} news" if subject else None
    outcome = extract_for_urls(urls, query=query, api_key=api_key)
    enriched = 0
    failed = 0
    for result in top:
        if result.url in outcome["extracted"]:
            result.full_content = outcome["extracted"][result.url]
            enriched += 1
        elif result.url in outcome["failed"]:
            failed += 1
    return {"enriched": enriched, "failed": failed}
