"""Date parsing and the strict last-30-days window.

Tavily returns published_date in more than one format. The official
example on docs.tavily.com shows an RFC-style string such as
"Tue, 11 Mar 2025 17:00:00 GMT". Other sources show ISO dates.
This module accepts both, plus plain YYYY-MM-DD, and returns None
when a date cannot be parsed, instead of guessing a date.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from email.utils import parsedate_to_datetime


def parse_published_date(value) -> date | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    # Plain YYYY-MM-DD, or ISO datetime.
    try:
        if len(text) == 10 and text[4] == "-" and text[7] == "-":
            return date.fromisoformat(text)
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return parsed.date()
    except ValueError:
        pass
    # RFC 2822 / GMT style, e.g. "Tue, 11 Mar 2025 17:00:00 GMT".
    try:
        return parsedate_to_datetime(text).date()
    except (TypeError, ValueError):
        return None


def meeting_window(meeting: date, today: date | None = None) -> tuple[date, date]:
    """Return (window_start, window_end) for the 30 days before a meeting.

    If the meeting is in the future, the window ends today, because
    future developments cannot be searched yet. The window is 30 days
    long inclusive of the end date: start = end - 29 days would give
    30 calendar days, but this project uses start = end - 30 days so
    a result exactly 30 days old is still kept. That choice is
    documented here and covered by a test.
    """
    if today is None:
        today = date.today()
    window_end = min(meeting, today)
    window_start = window_end - timedelta(days=30)
    return window_start, window_end


def in_window(d: date | None, start: date, end: date) -> bool:
    if d is None:
        return False
    return start <= d <= end
