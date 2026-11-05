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
    response = requests.post(
        BASE_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=DEFAULT_TIMEOUT_SECONDS,
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
