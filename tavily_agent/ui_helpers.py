"""Shared helpers for the web UIs. No web framework import here.

Both web UIs (the standard library web_ui.py and the Streamlit
app.py) build briefings through the same tavily_agent pipeline, and
both use these helpers to validate input and to shape a briefing
for display. Keeping the helpers framework-free means they can be
unit tested without installing any web framework.
"""
from __future__ import annotations

from datetime import date

from .briefing import build_briefing
from .dates import meeting_window

LIMITATION_NOTE = (
    "Honest limit: the direct API route from this environment still "
    "returns HTTP 401 with the stored credential, while the same "
    "Tavily key works in the Playground. Live briefings built from "
    "Playground results prove the pipeline on real Tavily data, not "
    "the direct API client route. Playground snippets are truncated "
    "at about 100 characters, exactly as returned."
)


def validate_inputs(subject: str, meeting_text: str):
    """Return (subject, meeting_date, error).

    subject and meeting_date are set only when both inputs are valid;
    otherwise error holds a plain message and the other two are None.
    """
    clean_subject = (subject or "").strip()
    if not clean_subject:
        return None, None, "Company or person name is required."
    clean_meeting = (meeting_text or "").strip()
    if not clean_meeting:
        return None, None, "Meeting date is required."
    try:
        meeting = date.fromisoformat(clean_meeting)
    except ValueError:
        return None, None, "Meeting date must be YYYY-MM-DD."
    return clean_subject, meeting, None


def briefing_counts(briefing) -> dict:
    """Kept and dropped counts for display, in one place."""
    return {
        "kept": len(briefing.results),
        "dropped_old": briefing.dropped_old_count,
        "dropped_duplicates": briefing.dropped_duplicate_count,
        "dropped_truncated_url": briefing.dropped_truncated_url_count,
        "dropped_profile": briefing.dropped_profile_count,
        "summary_excluded": getattr(briefing, "summary_excluded_count", 0),
    }


def format_briefing_for_display(briefing) -> dict:
    """Shape a Briefing into plain display data.

    Titles, URLs, dates, and snippets are copied exactly, never
    rewritten. Every development keeps its source URL.
    """
    start, end = briefing.window_start, briefing.window_end
    developments = []
    for result in briefing.results:
        developments.append({
            "title": result.title,
            "url": result.url,
            "date": result.published.isoformat() if result.published else "date unknown",
            "snippet": result.snippet,
            "full_content": getattr(result, "full_content", "") or "",
            "category": result.category,
        })
    return {
        "subject": briefing.subject,
        "meeting_date": briefing.meeting_date.isoformat(),
        "window": f"{start.isoformat()} to {end.isoformat()}",
        "mode": briefing.mode,
        "summary_mode": briefing.summary_mode,
        "summary": briefing.summary,
        "counts": briefing_counts(briefing),
        "developments": developments,
        "discussion_points": list(briefing.discussion_points),
        "open_questions": list(briefing.open_questions),
        "source_note": briefing.source_note,
        "limitation_note": LIMITATION_NOTE,
    }


def build_briefing_from_inputs(subject: str, meeting: date, raw: list,
                               mode: str = "mock",
                               summary_mode: str = "extractive",
                               today: date | None = None):
    """Build a briefing through the shared pipeline.

    Thin wrapper over build_briefing so both web UIs call the same
    code path with the same arguments.
    """
    return build_briefing(subject, meeting, raw, mode=mode,
                          summary_mode=summary_mode, today=today)


def window_for_meeting(meeting: date, today: date | None = None):
    """The 30-day window for a meeting date, capped at today."""
    return meeting_window(meeting, today=today)
