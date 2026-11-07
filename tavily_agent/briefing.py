"""Briefing pipeline: filter, deduplicate, sort, summarise, question.

Anti-hallucination rules enforced here:
1. A dated result outside the window is dropped, never rewritten.
2. An undated result is kept but flagged date_unknown, so the
   briefing can say its date could not be verified.
3. Every key development in the output carries its source URL.
4. An empty result set produces an explicit "No results" briefing
   with zero invented developments, discussion points, or questions
   about specific events. Only generic preparation questions are
   allowed in that case, and they are labelled as generic.
"""
from __future__ import annotations

import re
from datetime import date
from urllib.parse import urlparse

from .dates import in_window, meeting_window
from .models import Briefing, SearchResult

CATEGORY_LABELS = {
    "news": "News",
    "launches": "Launches and product updates",
    "hires": "Hires and leadership",
    "funding": "Funding, deals and partnerships",
}


def normalise_url(url: str) -> str:
    parsed = urlparse((url or "").strip().lower())
    host = parsed.netloc
    if host.startswith("www."):
        host = host[4:]
    path = parsed.path.rstrip("/")
    return f"{host}{path}"


def filter_and_dedupe(raw: list, start: date, end: date):
    """Return (kept, dropped_old, dropped_duplicates).

    raw items are dicts with keys title, url, snippet, published
    (a date or None), score, category. Dated items outside the
    window are dropped. Undated items are kept with date_unknown.
    Duplicates share a normalised URL; the highest-score copy wins.
    """
    by_url: dict[str, SearchResult] = {}
    dropped_old = 0
    dropped_dup = 0
    for item in raw:
        url = (item.get("url") or "").strip()
        if not url:
            continue
        published = item.get("published")
        if published is not None and not in_window(published, start, end):
            dropped_old += 1
            continue
        result = SearchResult(
            title=item.get("title", "Untitled result"),
            url=url,
            snippet=item.get("snippet", "") or "",
            published=published,
            score=float(item.get("score") or 0.0),
            category=item.get("category", "news"),
        )
        key = normalise_url(url)
        if key in by_url:
            dropped_dup += 1
            if result.score > by_url[key].score:
                by_url[key] = result
        else:
            by_url[key] = result
    kept = sorted(
        by_url.values(),
        key=lambda r: (r.published is None, r.published or date.min, -r.score),
        reverse=False,
    )
    # Sort dated newest first, undated last. The key above puts
    # dated items first (False < True), then by date ascending, so
    # reverse the dated block explicitly for readability.
    dated = sorted([r for r in kept if r.published], key=lambda r: r.published, reverse=True)
    undated = [r for r in kept if not r.published]
    return dated + undated, dropped_old, dropped_dup


def first_sentence(text: str) -> str:
    text = re.sub(r"\s+", " ", (text or "").strip())
    if not text:
        return ""
    match = re.split(r"(?<=[.!?])\s+", text, maxsplit=1)
    sentence = match[0].strip()
    return sentence[:300]


def mentions_subject(result, subject: str) -> bool:
    """True only when the subject name appears in BOTH the title and
    the snippet (case-insensitive, subject string only, no short
    forms or parent company names). A development is eligible for
    the Top findings in the summary only when this is true. This
    matters because some returned snippets are boilerplate or
    off-topic next to their titles, for example a snippet about an
    unrelated crash under a title that does name the subject. Such
    a development stays in Key developments in full, with its source
    link, but its snippet is not quoted in the summary."""
    name = (subject or "").strip().lower()
    if not name:
        return True
    return name in (result.title or "").lower() and name in (result.snippet or "").lower()


def summary_eligible_results(results, subject: str) -> list:
    """Kept developments eligible for the summary Top findings."""
    return [r for r in results if mentions_subject(r, subject)]


def build_briefing(subject: str, meeting: date, raw: list,
                   mode: str = "mock", summary_mode: str = "extractive",
                   today: date | None = None) -> Briefing:
    start, end = meeting_window(meeting, today=today)
    kept, dropped_old, dropped_dup = filter_and_dedupe(raw, start, end)

    if not kept:
        return Briefing(
            subject=subject, meeting_date=meeting,
            window_start=start, window_end=end, results=[],
            summary=(
                f"No results were found for '{subject}' in the "
                f"window {start.isoformat()} to {end.isoformat()}. "
                "No developments are listed, because none were verified."
            ),
            discussion_points=[
                "Ask what has changed for this company or person since the last meeting, if anything is not yet public.",
            ],
            open_questions=[
                "Is there a more specific company name, product name, or person name that would return better search results?",
                "Are there announcements on the company site or social channels that search did not return?",
            ],
            mode=mode, summary_mode=summary_mode,
            dropped_old_count=dropped_old,
            dropped_duplicate_count=dropped_dup,
        )

    counts = {}
    for result in kept:
        counts[result.category] = counts.get(result.category, 0) + 1
    count_text = ", ".join(
        f"{n} {CATEGORY_LABELS.get(cat, cat).lower()}"
        for cat, n in sorted(counts.items())
    )
    eligible = summary_eligible_results(kept, subject)
    summary_excluded = len(kept) - len(eligible)
    top_snippets = [first_sentence(r.snippet) for r in eligible[:3]]
    top_snippets = [s for s in top_snippets if s]
    summary = (
        f"Found {len(kept)} result(s) for '{subject}' in the "
        f"window {start.isoformat()} to {end.isoformat()} ({count_text}). "
    )
    if top_snippets:
        summary += "Top findings: " + " ".join(top_snippets)
    else:
        summary += (
            "No top finding names the subject directly in both its "
            "title and snippet; see Key developments below."
        )

    discussion_points = []
    for result in kept[:5]:
        date_text = result.published.isoformat() if result.published else "date unknown"
        discussion_points.append(
            f"Discuss: {result.title} ({date_text}). "
            "What decision or action does this require in the meeting?"
        )
    discussion_points = discussion_points[:5]

    open_questions = []
    latest = kept[0].published.isoformat() if kept and kept[0].published else None
    if latest:
        open_questions.append(
            f"Has anything changed since the latest dated finding ({latest}) that is not yet covered here?"
        )
    for result in kept[:3]:
        open_questions.append(
            f"What is the current status or next step for: {result.title}?"
        )
    undated = [r for r in kept if r.date_unknown]
    if undated:
        open_questions.append(
            "Can the meeting confirm dates for the findings marked 'date unknown', "
            "since Tavily did not return a published date for them?"
        )
    open_questions = open_questions[:5]

    return Briefing(
        subject=subject, meeting_date=meeting,
        window_start=start, window_end=end, results=kept,
        summary=summary, discussion_points=discussion_points,
        open_questions=open_questions, mode=mode,
        summary_mode=summary_mode,
        dropped_old_count=dropped_old,
        dropped_duplicate_count=dropped_dup,
        summary_excluded_count=summary_excluded,
    )
