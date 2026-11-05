"""Data models. No network calls here, so tests stay fast and offline."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str = ""
    published: Optional[date] = None
    score: float = 0.0
    category: str = "news"
    date_unknown: bool = False

    def __post_init__(self) -> None:
        self.title = (self.title or "Untitled result").strip()
        self.url = (self.url or "").strip()
        self.snippet = (self.snippet or "").strip()
        self.category = (self.category or "news").strip().lower()
        if self.published is None:
            self.date_unknown = True


@dataclass
class Briefing:
    subject: str
    meeting_date: date
    window_start: date
    window_end: date
    results: list = field(default_factory=list)
    summary: str = ""
    discussion_points: list = field(default_factory=list)
    open_questions: list = field(default_factory=list)
    mode: str = "mock"  # live | mock | extractive fallback is noted in summary_mode
    summary_mode: str = "extractive"
    dropped_old_count: int = 0
    dropped_duplicate_count: int = 0
    dropped_truncated_url_count: int = 0
    dropped_profile_count: int = 0
    source_note: str = ""
