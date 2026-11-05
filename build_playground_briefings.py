#!/usr/bin/env python3
"""Build live briefings from the Tavily Playground transcription.

Reads examples/live-playground-2026-11-05.json (60 results transcribed
exactly as shown in the Tavily API Playground on 2026-11-05) and feeds
them through the existing tavily_agent pipeline (dates, window filter,
deduplication, Markdown/PDF render). No call to api.tavily.com is made.

Honesty drops applied BEFORE the pipeline, tracked separately:
  - url_truncated: the Playground display cut the source URL, so the
    link cannot be verified. Dropped, counted as dropped_truncated_url.
  - Tavily knowledge-company pages (tavily.com/knowledge/company/...):
    company profiles, not dated developments, no published_date.
    Dropped, counted as dropped_profile.
The pipeline itself then drops dated results outside the 30-day window
(dropped_old) and duplicates by normalised URL (dropped_duplicates).
Undated results are kept only if their URL is complete and they are
not a profile page, and are flagged "date unknown" in the briefing.

Usage:
    python3 build_playground_briefings.py

Outputs: examples/live-<company>/briefing.md and briefing.pdf.
This overwrites the EMPTY Nov 4 files in examples/live-openai/ only.
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_DIR))

from tavily_agent.briefing import build_briefing
from tavily_agent.dates import parse_published_date
from tavily_agent.render import render_markdown, render_pdf

MEETING = date(2026, 11, 5)
JSON_PATH = PROJECT_DIR / "examples" / "live-playground-2026-11-05.json"
COMPANIES = ["OpenAI", "Google", "Microsoft"]
SLUGS = {"OpenAI": "openai", "Google": "google", "Microsoft": "microsoft"}

SOURCE_NOTE = (
    "LIVE via Tavily Playground, Nov 5, 2026. This briefing is built from "
    "20 Tavily Search results (topic news, basic depth, last 30 days) "
    "gathered in the Tavily API Playground while signed in as "
    "pakmultilinks@gmail.com. The Playground JSON view truncates long "
    "snippets at about 100 characters, so each snippet below is the "
    "truncated extract exactly as returned, never a fuller text. Results "
    "whose source URL was truncated in the Playground display were dropped "
    "because the link cannot be verified, and Tavily knowledge-company "
    "profile pages were dropped because they are profiles, not dated "
    "developments. Every development kept here carries its complete source "
    "URL and its published date, or 'date unknown' if none was shown."
)

PROFILE_PREFIX = "https://tavily.com/knowledge/company/"


def main() -> int:
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    results = data["results"]
    print(f"Loaded {len(results)} transcribed results from {JSON_PATH.name}")

    totals = {"kept": 0, "trunc_url": 0, "profile": 0, "old": 0, "dup": 0}
    for company in COMPANIES:
        company_results = [r for r in results if r["company"] == company]
        dropped_trunc = 0
        dropped_profile = 0
        raw: list[dict] = []
        for item in company_results:
            url = (item.get("url") or "").strip()
            if item.get("url_truncated"):
                dropped_trunc += 1
                continue
            if url.startswith(PROFILE_PREFIX):
                dropped_profile += 1
                continue
            raw.append({
                "title": item.get("title", "Untitled result"),
                "url": url,
                "snippet": item.get("content", "") or "",
                "published": parse_published_date(item.get("published_date")),
                "score": 0.0,
                "category": item.get("category", "news"),
            })
        briefing = build_briefing(
            company, MEETING, raw, mode="live",
            summary_mode="extractive", today=MEETING,
        )
        briefing.dropped_truncated_url_count = dropped_trunc
        briefing.dropped_profile_count = dropped_profile
        briefing.source_note = SOURCE_NOTE

        out_dir = PROJECT_DIR / "examples" / f"live-{SLUGS[company]}"
        out_dir.mkdir(parents=True, exist_ok=True)
        md_path = out_dir / "briefing.md"
        pdf_path = out_dir / "briefing.pdf"
        md_text = render_markdown(briefing)
        md_path.write_text(md_text, encoding="utf-8")
        render_pdf(briefing, str(pdf_path))

        # Smoke checks: every kept URL must appear in the Markdown,
        # and the PDF must start with a PDF header.
        for result in briefing.results:
            assert result.url in md_text, f"URL missing from MD: {result.url}"
        assert pdf_path.read_bytes()[:5] == b"%PDF-", f"Bad PDF header: {pdf_path}"
        assert "LIVE via Tavily Playground" in md_text

        print(
            f"{company}: total {len(company_results)}  kept {len(briefing.results)}  "
            f"dropped_old {briefing.dropped_old_count}  "
            f"dropped_duplicates {briefing.dropped_duplicate_count}  "
            f"dropped_truncated_url {dropped_trunc}  "
            f"dropped_profile {dropped_profile}"
        )
        print(f"  Markdown: {md_path}")
        print(f"  PDF: {pdf_path}")
        totals["kept"] += len(briefing.results)
        totals["trunc_url"] += dropped_trunc
        totals["profile"] += dropped_profile
        totals["old"] += briefing.dropped_old_count
        totals["dup"] += briefing.dropped_duplicate_count

    print(
        f"TOTAL: kept {totals['kept']}  dropped_old {totals['old']}  "
        f"dropped_duplicates {totals['dup']}  "
        f"dropped_truncated_url {totals['trunc_url']}  "
        f"dropped_profile {totals['profile']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
