"""Demo mode data for the Streamlit app. No web framework import here.

Demo mode is the default in app.py. It shows the three prebuilt
live briefings from Nov 5, 2026 (OpenAI, Google, Microsoft), with
no Tavily call and no owner key used. The briefing text is read
from the committed Markdown files, so what the demo shows is
exactly what is in the repo. Kept counts are parsed from the
briefing header, never hardcoded, so they stay truthful if the
briefings are rebuilt.

Live mode is separate: it uses a visitor key for that session
only. set_visitor_key only sets an environment variable in
memory; it never writes to disk. clear_visitor_key removes it.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
LIVE_DIR = PROJECT_DIR / "examples"

DEMO_COMPANIES = [
    ("OpenAI", "openai"),
    ("Google", "google"),
    ("Microsoft", "microsoft"),
]

DEMO_NOTE = (
    "Demo data: prebuilt live briefings from Nov 5, 2026, built "
    "from 60 real Tavily Playground results (37 kept: OpenAI 14, "
    "Google 15, Microsoft 8). No Tavily call is made in demo mode, "
    "and no key is used. For a fresh briefing, switch to Live mode "
    "and enter your own Tavily key."
)


def demo_companies() -> list[tuple[str, str]]:
    """Return the (company, slug) pairs shown in demo mode."""
    return list(DEMO_COMPANIES)


def load_demo_briefing(slug: str) -> dict:
    """Load one prebuilt live briefing by slug.

    Returns company, meeting date, window, kept count parsed
    from the header, the full Markdown text, and the PDF path.
    Raises FileNotFoundError when the briefing file is missing,
    and ValueError when the header cannot be parsed.
    """
    slugs = {slug for _, slug in DEMO_COMPANIES}
    if slug not in slugs:
        raise ValueError(f"Unknown demo company slug: {slug}.")
    md_path = LIVE_DIR / f"live-{slug}" / "briefing.md"
    pdf_path = LIVE_DIR / f"live-{slug}" / "briefing.pdf"
    text = md_path.read_text(encoding="utf-8")
    title = re.search(r"^# Pre-meeting briefing: (.+)$", text, re.MULTILINE)
    kept = re.search(r"Results kept: (\d+)", text)
    meeting = re.search(r"^Meeting date: (\d{4}-\d{2}-\d{2})$", text, re.MULTILINE)
    window = re.search(r"^Search window: (.+) \(last 30 days", text, re.MULTILINE)
    if not title or not kept or not meeting:
        raise ValueError(f"Could not parse demo briefing header: {md_path}.")
    return {
        "company": title.group(1).strip(),
        "slug": slug,
        "meeting_date": meeting.group(1),
        "window": window.group(1).strip() if window else "",
        "kept": int(kept.group(1)),
        "markdown": text,
        "pdf_path": pdf_path,
        "pdf_exists": pdf_path.exists(),
    }


def live_mode_available(visitor_key: str | None = None,
                        secrets_key: str | None = None) -> tuple[bool, str | None]:
    """Return (available, source) for live mode.

    source is "visitor" when a visitor key was entered, "secrets"
    when only a deployment secret is present, and None when no
    key is available. Demo mode does not call this.
    """
    if visitor_key and visitor_key.strip():
        return True, "visitor"
    if secrets_key and str(secrets_key).strip():
        return True, "secrets"
    return False, None


def set_visitor_key(key: str) -> None:
    """Keep a visitor key in memory for this session only.

    It is set as an environment variable in the running process
    and is never written to a file. Call clear_visitor_key to
    remove it.
    """
    os.environ["TAVILY_API_KEY"] = (key or "").strip()


def clear_visitor_key() -> None:
    """Remove a visitor key from memory."""
    os.environ.pop("TAVILY_API_KEY", None)
