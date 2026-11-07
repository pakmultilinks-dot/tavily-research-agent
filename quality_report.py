#!/usr/bin/env python3
"""Measure briefing quality from the committed live artefacts.

Reads examples/live-playground-2026-11-05.json (60 transcribed
Tavily Playground results, Nov 5, 2026) and the three committed
briefing Markdown files, rebuilds each briefing through the
existing pipeline with the same honesty drops as
build_playground_briefings.py, and reports only measured
numbers. No network call, no key, no new data is invented.

Honesty drops, same as the builder, in the same order:
  1. url_truncated: the Playground display cut the source URL,
     so the link cannot be verified.
  2. Tavily knowledge-company pages (tavily.com/knowledge/company/):
     company profiles, not dated developments.
The pipeline then drops dated results outside the 30-day window
and duplicates by normalised URL. Undated results are kept only
when their URL is complete and they are not a profile page.

Measured per company and in total:
  - kept per company, and dropped per reason (truncated URL,
    profile page, duplicates, too old)
  - share of kept developments with a dated result
  - share of kept developments with a source URL
  - share whose title and snippet both name the subject
    (the relevance rule for the Top findings)
  - date range covered by the kept dated results
  - categories covered per company
  - developments with full content from Tavily Extract
    (0 now, because enriching is off by default)

The committed Markdown headers are parsed and cross-checked
against the rebuild, so a mismatch would show up here instead
of silently reaching a judge.

Usage:
    python3 quality_report.py

Output: plain text report on stdout. To save it:
    python3 quality_report.py > QUALITY.md
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_DIR))

from tavily_agent.briefing import build_briefing, summary_eligible_results
from tavily_agent.dates import parse_published_date

JSON_PATH = PROJECT_DIR / "examples" / "live-playground-2026-11-05.json"
MEETING = date(2026, 11, 5)
COMPANIES = ["OpenAI", "Google", "Microsoft"]
SLUGS = {"OpenAI": "openai", "Google": "google", "Microsoft": "microsoft"}
PROFILE_PREFIX = "https://tavily.com/knowledge/company/"
CATEGORY_LABELS = {
    "news": "news",
    "launches": "launches and product updates",
    "hires": "hires and leadership",
    "funding": "funding, deals and partnerships",
}


def is_profile_url(url: str) -> bool:
    """True when the URL is a Tavily knowledge-company profile page."""
    return (url or "").strip().startswith(PROFILE_PREFIX)


def parse_md_header(text: str) -> dict:
    """Parse kept/dropped counts from a committed briefing header.

    Returns a dict with kept, dropped_old, dropped_duplicates,
    dropped_truncated_url, dropped_profile, each an int or None
    when the header does not carry that count.
    """
    def find(pattern: str):
        match = re.search(pattern, text)
        return int(match.group(1)) if match else None

    return {
        "kept": find(r"Results kept: (\d+)"),
        "dropped_old": find(r"Dropped as too old: (\d+)"),
        "dropped_duplicates": find(r"Dropped as duplicates: (\d+)"),
        "dropped_truncated_url": find(r"Dropped as truncated URL: (\d+)"),
        "dropped_profile": find(r"Dropped as profile page: (\d+)"),
    }


def share(numerator: int, denominator: int) -> str:
    """Format a measured share as 'n/d (p%)', or 'n/a' when empty."""
    if denominator == 0:
        return f"{numerator}/0 (n/a)"
    return f"{numerator}/{denominator} ({100 * numerator / denominator:.0f}%)"


def measure_company(company: str, items: list,
                    meeting: date = MEETING, today: date = MEETING) -> dict:
    """Measure one company from its transcribed JSON results.

    Applies the builder drops, then the pipeline, and measures
    the kept briefing. Returns counts and shares, no invented
    values: every number comes from the inputs given.
    """
    dropped_trunc = 0
    dropped_profile = 0
    raw: list[dict] = []
    for item in items:
        url = (item.get("url") or "").strip()
        if item.get("url_truncated"):
            dropped_trunc += 1
            continue
        if is_profile_url(url):
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
        company, meeting, raw, mode="live",
        summary_mode="extractive", today=today,
    )
    kept = briefing.results
    dated = [r for r in kept if r.published is not None]
    with_url = [r for r in kept if r.url]
    named = summary_eligible_results(kept, company)
    with_full = [r for r in kept if r.full_content]
    dates = sorted(r.published for r in dated)
    categories = sorted({r.category for r in kept})
    return {
        "company": company,
        "total": len(items),
        "kept": len(kept),
        "dropped_old": briefing.dropped_old_count,
        "dropped_duplicates": briefing.dropped_duplicate_count,
        "dropped_truncated_url": dropped_trunc,
        "dropped_profile": dropped_profile,
        "dated": (len(dated), len(kept)),
        "with_url": (len(with_url), len(kept)),
        "named_subject": (len(named), len(kept)),
        "with_full_content": (len(with_full), len(kept)),
        "date_range": (dates[0], dates[-1]) if dates else (None, None),
        "categories": categories,
    }


def measure_all(data: dict, meeting: date = MEETING) -> dict:
    """Measure every company in the source JSON, plus totals.

    Totals are sums of the per-company counts, so the total
    shares are measured from the same kept developments, not
    from rounded percentages.
    """
    results = data["results"]
    per_company = {}
    for company in COMPANIES:
        items = [r for r in results if r.get("company") == company]
        per_company[company] = measure_company(company, items, meeting, meeting)
    total = {
        "company": "Total",
        "total": sum(m["total"] for m in per_company.values()),
        "kept": sum(m["kept"] for m in per_company.values()),
        "dropped_old": sum(m["dropped_old"] for m in per_company.values()),
        "dropped_duplicates": sum(m["dropped_duplicates"] for m in per_company.values()),
        "dropped_truncated_url": sum(m["dropped_truncated_url"] for m in per_company.values()),
        "dropped_profile": sum(m["dropped_profile"] for m in per_company.values()),
        "dated": (
            sum(m["dated"][0] for m in per_company.values()),
            sum(m["dated"][1] for m in per_company.values()),
        ),
        "with_url": (
            sum(m["with_url"][0] for m in per_company.values()),
            sum(m["with_url"][1] for m in per_company.values()),
        ),
        "named_subject": (
            sum(m["named_subject"][0] for m in per_company.values()),
            sum(m["named_subject"][1] for m in per_company.values()),
        ),
        "with_full_content": (
            sum(m["with_full_content"][0] for m in per_company.values()),
            sum(m["with_full_content"][1] for m in per_company.values()),
        ),
        "date_range": (
            min(m["date_range"][0] for m in per_company.values()
                if m["date_range"][0] is not None),
            max(m["date_range"][1] for m in per_company.values()
                if m["date_range"][1] is not None),
        ),
        "categories": sorted({c for m in per_company.values()
                              for c in m["categories"]}),
    }
    return {"per_company": per_company, "total": total}


def format_company(m: dict) -> str:
    """Format one measured company (or the total) as plain text."""
    start, end = m["date_range"]
    date_range = f"{start.isoformat()} to {end.isoformat()}" if start else "no dated results"
    categories = ", ".join(CATEGORY_LABELS.get(c, c) for c in m["categories"])
    category_note = f"{categories} ({len(m['categories'])} of 4)" if m["categories"] else "none"
    lines = [
        f"{m['company']}: total {m['total']}, kept {m['kept']}, "
        f"dropped as truncated URL {m['dropped_truncated_url']}, "
        f"profile page {m['dropped_profile']}, "
        f"duplicates {m['dropped_duplicates']}, "
        f"too old {m['dropped_old']}",
        f"  dated result: {share(*m['dated'])}",
        f"  with source URL: {share(*m['with_url'])}",
        f"  title and snippet both name the subject: {share(*m['named_subject'])}",
        f"  date range covered: {date_range}",
        f"  categories covered: {category_note}",
        f"  with full content (Tavily Extract): {share(*m['with_full_content'])}",
    ]
    return "\n".join(lines)


def format_report(measured: dict, md_check: dict) -> str:
    """Format the full plain text quality report."""
    lines = [
        "Tavily Research Agent, briefing quality report",
        f"Measured: {date.today().isoformat()}",
        "Source: examples/live-playground-2026-11-05.json "
        "(60 transcribed Tavily Playground results, Nov 5, 2026)",
        "Reproduce: python3 quality_report.py",
        "Method: each company rebuilt through the same pipeline and "
        "honesty drops as build_playground_briefings.py. Numbers "
        "below are measured from that rebuild and cross-checked "
        "against the committed briefing Markdown headers.",
        "",
        "Per company",
    ]
    for company in COMPANIES:
        lines.append(format_company(measured["per_company"][company]))
    lines.append("")
    lines.append("Total")
    lines.append(format_company(measured["total"]))
    lines.append("")
    lines.append("Cross-check against the committed briefing Markdown headers")
    for company in COMPANIES:
        check = md_check[company]
        lines.append(f"  {company}: kept and dropped counts match the rebuild: {check}")
    lines.append("")
    lines.append("Limits, read before judging")
    lines.append(
        "  The named-subject share is low mainly because the "
        "Playground JSON view truncates snippets at about 100 "
        "characters, so a snippet often does not name the subject "
        "even when the title does. Those developments are still "
        "listed in full, with source links, in Key developments; "
        "only the Top findings quote the named ones. Tavily "
        "Extract (off by default) can add full content for the "
        "top 8 developments per company, but it has not been run "
        "live yet, so with_full_content is 0 here. The direct "
        "API route is still unproven (HTTP 401 here), so these "
        "numbers measure the Playground briefings, not a live "
        "API run."
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    measured = measure_all(data, MEETING)
    md_check = {}
    for company in COMPANIES:
        md_path = PROJECT_DIR / "examples" / f"live-{SLUGS[company]}" / "briefing.md"
        header = parse_md_header(md_path.read_text(encoding="utf-8"))
        m = measured["per_company"][company]
        md_check[company] = (
            "yes" if header["kept"] == m["kept"]
            and header["dropped_old"] == m["dropped_old"]
            and header["dropped_duplicates"] == m["dropped_duplicates"]
            and header["dropped_truncated_url"] == m["dropped_truncated_url"]
            and header["dropped_profile"] == m["dropped_profile"]
            else "NO, header and rebuild disagree"
        )
    print(format_report(measured, md_check), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
