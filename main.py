#!/usr/bin/env python3
"""CLI for the Tavily Research Agent.

Live mode (default):
    export TAVILY_API_KEY='your-key-here'
    python3 main.py --subject "Acme Corp" --meeting 2026-11-10 --out examples/acme

Mock / offline mode (fixtures only, no network, no key needed):
    python3 main.py --subject "Example Company" --meeting 2026-11-10 --mock --out examples/sample_briefing

The --out value is a file stem: --out examples/sample_briefing writes
examples/sample_briefing.md and examples/sample_briefing.pdf.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from tavily_agent.briefing import build_briefing
from tavily_agent.dates import meeting_window, parse_published_date
from tavily_agent.render import render_markdown, render_pdf
from tavily_agent.summarizer import extractive_summary, try_llm_summary
from tavily_agent.tavily_client import search_all_categories


def load_fixtures(path: str, subject: str) -> list:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    raw = []
    for item in data.get("results", []):
        raw.append({
            "title": item.get("title", "Untitled result"),
            "url": item.get("url", ""),
            "snippet": item.get("content", "") or item.get("snippet", ""),
            "published": parse_published_date(item.get("published_date")),
            "score": float(item.get("score") or 0.0),
            "category": item.get("category", "news"),
        })
    return raw


def main() -> int:
    parser = argparse.ArgumentParser(description="Tavily Research Agent: pre-meeting briefing")
    parser.add_argument("--subject", required=True, help="Company or person name")
    parser.add_argument("--meeting", required=True, help="Meeting date, YYYY-MM-DD")
    parser.add_argument("--out", required=True, help="Output file stem, e.g. examples/sample_briefing")
    parser.add_argument("--mock", action="store_true", help="Use local fixtures, no Tavily call")
    parser.add_argument("--fixtures", default="examples/fixtures.json")
    parser.add_argument("--max-results", type=int, default=5)
    parser.add_argument("--search-depth", default="basic", choices=["basic", "advanced"])
    args = parser.parse_args()

    meeting = date.fromisoformat(args.meeting)
    start, end = meeting_window(meeting)

    if args.mock:
        raw = load_fixtures(args.fixtures, args.subject)
        mode = "mock"
    else:
        raw = search_all_categories(
            args.subject, start.isoformat(), end.isoformat(),
            max_results=args.max_results, search_depth=args.search_depth,
        )
        mode = "live"

    briefing = build_briefing(args.subject, meeting, raw, mode=mode)

    # Optional LLM summary: only replaces the extractive summary text
    # inside the summary field if it succeeds, and the mode is labelled.
    # It never adds new developments.
    if briefing.results:
        llm_text, llm_mode = try_llm_summary(briefing.results, args.subject)
        if llm_text:
            briefing.summary = (
                f"Found {len(briefing.results)} result(s) for "
                f"'{args.subject}' in the window {start.isoformat()} to "
                f"{end.isoformat()}. LLM summary: {llm_text}"
            )
            briefing.summary_mode = llm_mode
        else:
            briefing.summary_mode = "extractive"

    out_stem = Path(args.out)
    out_stem.parent.mkdir(parents=True, exist_ok=True)
    md_path = out_stem.with_suffix(".md")
    pdf_path = out_stem.with_suffix(".pdf")
    md_path.write_text(render_markdown(briefing), encoding="utf-8")
    render_pdf(briefing, str(pdf_path))
    print(f"Subject: {args.subject}")
    print(f"Meeting: {meeting.isoformat()}  Window: {start.isoformat()} to {end.isoformat()}")
    print(f"Mode: {mode}  Summary mode: {briefing.summary_mode}")
    print(f"Kept: {len(briefing.results)}  Dropped old: {briefing.dropped_old_count}  Dropped duplicates: {briefing.dropped_duplicate_count}")
    print(f"Markdown: {md_path}")
    print(f"PDF: {pdf_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
