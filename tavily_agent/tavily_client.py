"""Tavily Search API client. Verified parameters only.

Verified 2026-11-03 from Tavily docs and SDK references (see README):
- Endpoint: POST https://api.tavily.com/search
- Auth header: Authorization: Bearer <TAVILY_API_KEY>
- Content-Type: application/json
- Body: query (required), topic, search_depth, max_results,
  time_range, start_date, end_date, include_domains, exclude_domains,
  include_answer, include_raw_content.
- Response: results[] with title, url, content, score, published_date.

NOT sent by this client, because they were not verified on the
official docs page fetched for this project:
- include_published_date (unverified; published_date handling is
  documented in the SDK as tied to topic=news, so this client uses
  topic=news and handles a missing date explicitly instead).

The key is read ONLY from the TAVILY_API_KEY environment variable.
It is never hardcoded and never written to any file by this code.
"""
from __future__ import annotations

import json
import os

import requests

BASE_URL = "https://api.tavily.com/search"
DEFAULT_TIMEOUT_SECONDS = 30
MAX_ATTEMPTS = 2  # one first try plus one retry, on timeout only, never on 401

# The tvly- prefix comes from a secondary source (Tavily MCP
# troubleshooting notes) and is unverified for this project, so a
# key that does not start with it is only warned about, never
# rejected on format alone. A wrong key is rejected by Tavily
# with HTTP 401, and that error names the fix.
KEY_PREFIX = "tvly-"

AUTH_FIX_MESSAGE = (
    "Tavily rejected the key with HTTP 401 Unauthorized. "
    "Fix: open the Tavily dashboard at https://app.tavily.com/home, "
    "check Overview / API Keys, copy the active default dev key, "
    "and set it as TAVILY_API_KEY in your shell. "
    "Create a fresh key there first if the listed key looks old or "
    "revoked. Never paste a real key into source code, into a "
    "committed .env file, or into a chat message."
)


class TavilyAuthError(RuntimeError):
    """Raised when Tavily returns HTTP 401 for the supplied key."""


def key_format_warning(key: str) -> str | None:
    """Return a warning when a key does not look like a Tavily key.

    The tvly- prefix is unverified for this project, so this only
    warns, it never rejects a key. Returns None when the format
    looks right, or when the key is empty (the empty case is
    handled separately by get_api_key).
    """
    key = (key or "").strip()
    if not key:
        return None
    if not key.startswith(KEY_PREFIX):
        return (
            "The key does not start with tvly-, which is the format "
            "seen in Tavily troubleshooting notes. That prefix is "
            "unverified for this project, so the key was still sent, "
            "but double-check that it was copied in full from the "
            "Tavily dashboard, with no extra characters or spaces."
        )
    return None

CATEGORY_QUERIES = {
    "news": "{subject} news",
    "launches": "{subject} product launch OR new product OR announcement",
    "hires": "{subject} hires OR new hire OR appointment OR leadership",
    "funding": "{subject} funding OR investment OR acquisition OR partnership",
}


def get_api_key() -> str:
    key = os.environ.get("TAVILY_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "TAVILY_API_KEY is not set. Export it in your shell, for example:\n"
            "  export TAVILY_API_KEY='your-key-here'\n"
            "Never paste a real key into source code or into a .env file "
            "that is committed to git. See .env.example."
        )
    return key


def search_category(subject: str, category: str, start: str, end: str,
                    max_results: int = 5, search_depth: str = "basic") -> list[dict]:
    """Run one Tavily search for one category. Returns raw result dicts."""
    from .dates import parse_published_date  # local import, avoids cycles
    from .models import SearchResult  # noqa: F401  (kept for type clarity)

    api_key = get_api_key()
    query = CATEGORY_QUERIES[category].format(subject=subject)
    payload = {
        "query": query,
        "topic": "news",
        "search_depth": search_depth,
        "max_results": max_results,
        "time_range": "month",
        "start_date": start,
        "end_date": end,
        "include_answer": False,
        "include_raw_content": False,
    }
    response = None
    last_timeout = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = requests.post(
                BASE_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=DEFAULT_TIMEOUT_SECONDS,
            )
            break
        except requests.Timeout as exc:
            # One retry only, on timeout. Never retried on 401.
            last_timeout = exc
            if attempt == MAX_ATTEMPTS:
                raise RuntimeError(
                    "Tavily search timed out after one retry. "
                    "The request was sent twice and got no response. "
                    "Check the network, then try again. The key was "
                    "not logged and is not shown in this error."
                ) from exc
    if response is None:  # pragma: no cover - guarded by the loop above
        raise RuntimeError("Tavily search produced no response.") from last_timeout
    if response.status_code == 401:
        message = AUTH_FIX_MESSAGE
        warning = key_format_warning(api_key)
        if warning:
            message += " " + warning
        raise TavilyAuthError(message)
    if response.status_code == 403:
        raise RuntimeError(
            "Tavily returned HTTP 403 Forbidden. The key may lack "
            "access to this endpoint. Check the key in the Tavily "
            "dashboard. The key was not logged and is not shown here."
        )
    response.raise_for_status()
    data = response.json()
    raw_results = data.get("results", []) if isinstance(data, dict) else []
    parsed = []
    for item in raw_results:
        if not isinstance(item, dict) or not item.get("url"):
            continue
        parsed.append({
            "title": item.get("title", "Untitled result"),
            "url": item.get("url"),
            "snippet": item.get("content", "") or "",
            "published": parse_published_date(item.get("published_date")),
            "score": float(item.get("score") or 0.0),
            "category": category,
        })
    return parsed


def smoke_check() -> dict:
    """One small live search, reporting status only, never the key.

    Calls search_category once with max_results 1 for a fixed
    subject and today's window. Returns {"ok": True, "results": n}
    on success. On 401 it raises TavilyAuthError with the fix
    message. No key value is printed, logged, or returned. This
    is what live_smoke.py runs; it writes no files.
    """
    from datetime import date as _date
    from .dates import meeting_window as _window

    today = _date.today()
    start, end = _window(today, today=today)
    results = search_category(
        "OpenAI", "news", start.isoformat(), end.isoformat(),
        max_results=1,
    )
    return {"ok": True, "results": len(results)}


def search_all_categories(subject: str, start: str, end: str,
                          max_results: int = 5,
                          search_depth: str = "basic") -> list[dict]:
    """Run the four category searches and return one flat raw list."""
    all_results: list[dict] = []
    for category in CATEGORY_QUERIES:
        try:
            all_results.extend(
                search_category(subject, category, start, end,
                                max_results=max_results,
                                search_depth=search_depth)
            )
        except Exception as exc:  # keep one failing category from killing the briefing
            all_results.append({
                "title": f"Search failed for category '{category}': {exc}",
                "url": "",
                "snippet": "",
                "published": None,
                "score": 0.0,
                "category": category,
                "_error": True,
            })
    return [r for r in all_results if r.get("url")]
