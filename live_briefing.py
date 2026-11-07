#!/usr/bin/env python3
"""Live briefing runner using the custom.tavily connector.

This runner does NOT read TAVILY_API_KEY from the environment and
does NOT accept a key on the command line. It calls Tavily only
through ~/workspace/custom-connectors/custom.tavily/bin/tavily_search.py,
which obtains an hsurr: surrogate from the registered custom.tavily
connection. No credential value is printed, logged, or written to a
file by this script.

Usage:
    python3 live_briefing.py --subject "OpenAI" --meeting 2026-11-03 \
        --out examples/live-openai/briefing

Outputs: <out>.md and <out>.pdf, plus counts printed to stdout.
Live status: UNPROVEN live as of 2026-11-07. Calls to
api.tavily.com from this environment first timed out (Nov 3,
2026) and then returned HTTP 401 with the stored credential
(Nov 5, 2026), while the same Tavily key works in the Tavily
Playground. Full record: LIVE_TEST.md. Before running this
script, run python3 live_smoke.py with a fresh key in
TAVILY_API_KEY to check the direct route; it reports status
only and writes no files. The direct route client
(tavily_agent/tavily_client.py) now trims the key, rejects an
empty key before any network call, retries once only on
timeout, never on 401, and raises a clear error on 401 that
names the fix.
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
CONNECTOR_BIN = Path.home() / "workspace" / "custom-connectors" / "custom.tavily" / "bin"

sys.path.insert(0, str(PROJECT_DIR))
sys.path.insert(0, str(CONNECTOR_BIN))

from tavily_agent.briefing import build_briefing
from tavily_agent.dates import meeting_window, parse_published_date
from tavily_agent.render import render_markdown, render_pdf
from tavily_agent.tavily_client import CATEGORY_QUERIES

from tavily_search import search_tavily  # noqa: E402


def search_all_via_connector(subject: str, start: str, end: str,
                             max_results: int = 5,
                             search_depth: str = "basic"):
    """Run the four category searches via the connector.

    Returns (raw_results, per_category_counts, errors). A failing
    category is recorded in errors and does not kill the briefing.
    """
    raw: list[dict] = []
    counts: dict[str, int] = {}
    errors: list[str] = []
    for category, template in CATEGORY_QUERIES.items():
        query = template.format(subject=subject)
        try:
            data = search_tavily(
                query=query, topic="news", search_depth=search_depth,
                max_results=max_results, time_range="month",
                start_date=start, end_date=end, timeout=60,
            )
        except Exception as exc:  # noqa: BLE001 - record, do not invent results
            errors.append(f"{category}: {type(exc).__name__}: {exc}")
            counts[category] = 0
            continue
        results = data.get("results", []) if isinstance(data, dict) else []
        counts[category] = len(results)
        for item in results:
            if not isinstance(item, dict) or not item.get("url"):
                continue
            raw.append({
                "title": item.get("title", "Untitled result"),
                "url": item.get("url"),
                "snippet": item.get("content", "") or "",
                "published": parse_published_date(item.get("published_date")),
                "score": float(item.get("score") or 0.0),
                "category": category,
            })
    return raw, counts, errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Live Tavily briefing via custom.tavily")
    parser.add_argument("--subject", required=True)
    parser.add_argument("--meeting", required=True,
                        help="Meeting date, YYYY-MM-DD")
    parser.add_argument("--out", required=True,
                        help="Output file stem, e.g. examples/live-openai/briefing")
    parser.add_argument("--max-results", type=int, default=5)
    parser.add_argument("--search-depth", default="basic",
                        choices=["basic", "advanced"])
    args = parser.parse_args()

    meeting = date.fromisoformat(args.meeting)
    start, end = meeting_window(meeting, today=meeting)
    raw, counts, errors = search_all_via_connector(
        args.subject, start.isoformat(), end.isoformat(),
        max_results=args.max_results, search_depth=args.search_depth,
    )
    briefing = build_briefing(
        args.subject, meeting, raw, mode="live",
        summary_mode="extractive", today=meeting,
    )
    out_stem = Path(args.out)
    out_stem.parent.mkdir(parents=True, exist_ok=True)
    md_path = out_stem.with_suffix(".md")
    pdf_path = out_stem.with_suffix(".pdf")
    md_path.write_text(render_markdown(briefing), encoding="utf-8")
    render_pdf(briefing, str(pdf_path))
    print(f"Subject: {args.subject}")
    print(f"Meeting: {meeting.isoformat()}  Window: {start.isoformat()} to {end.isoformat()}")
    print(f"Mode: live  Summary mode: extractive")
    print(f"Raw results: {len(raw)}  Per category: {counts}")
    if errors:
        print(f"Category errors: {errors}")
    print(f"Kept: {len(briefing.results)}  Dropped old: {briefing.dropped_old_count}  Dropped duplicates: {briefing.dropped_duplicate_count}")
    print(f"Markdown: {md_path}")
    print(f"PDF: {pdf_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
