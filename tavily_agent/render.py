"""Render a Briefing to Markdown and PDF. No invented facts here.

Markdown keeps full source links. PDF keeps the same content in
plain text with URLs in parentheses, because reportlab does not
render Markdown links.
"""
from __future__ import annotations

import html

from .briefing import CATEGORY_LABELS


def render_markdown(b: object) -> str:
    lines = []
    lines.append(f"# Pre-meeting briefing: {b.subject}")
    lines.append("")
    lines.append(f"Meeting date: {b.meeting_date.isoformat()}")
    lines.append(f"Search window: {b.window_start.isoformat()} to {b.window_end.isoformat()} (last 30 days before the meeting, capped at today)")
    lines.append(f"Mode: {b.mode} | Summary mode: {b.summary_mode}")
    lines.append(f"Results kept: {len(b.results)} | Dropped as too old: {b.dropped_old_count} | Dropped as duplicates: {b.dropped_duplicate_count}")
    if b.dropped_truncated_url_count or b.dropped_profile_count:
        lines.append(f"Dropped as truncated URL: {b.dropped_truncated_url_count} | Dropped as profile page: {b.dropped_profile_count}")
    if b.source_note:
        lines.append("")
        lines.append(b.source_note)
    enriched = getattr(b, "extract_enriched_count", 0)
    failed = getattr(b, "extract_failed_count", 0)
    if enriched or failed:
        lines.append("")
        lines.append(
            f"Tavily Extract enriched {enriched} development(s) with "
            f"full content; {failed} URL(s) failed Extract and keep "
            "their search snippet as fallback. Dates and URLs are "
            "from the search result, never from Extract."
        )
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(b.summary)
    lines.append("")
    excluded = getattr(b, "summary_excluded_count", 0)
    if excluded:
        lines.append(
            f"Note: {excluded} kept development(s) below are not in the "
            "Top findings above, because the subject name does not appear "
            "in both their title and snippet. They are still listed in "
            "full, with source links, in Key developments."
        )
        lines.append("")
    if not b.results:
        lines.append("## Key developments")
        lines.append("")
        lines.append("No verified developments in this window. Nothing is listed here on purpose.")
        lines.append("")
    else:
        lines.append("## Key developments")
        lines.append("")
        by_category: dict[str, list] = {}
        for result in b.results:
            by_category.setdefault(result.category, []).append(result)
        for category in sorted(by_category):
            lines.append(f"### {CATEGORY_LABELS.get(category, category)}")
            lines.append("")
            for result in by_category[category]:
                date_text = result.published.isoformat() if result.published else "date unknown"
                lines.append(f"- **{result.title}** ({date_text})")
                lines.append(f"  Source: {result.url}")
                if result.snippet:
                    lines.append(f"  {result.snippet[:400]}")
                full = getattr(result, "full_content", "") or ""
                if full:
                    lines.append(f"  Full content (Tavily Extract): {full[:800]}")
            lines.append("")
    lines.append("## Discussion points")
    lines.append("")
    for point in b.discussion_points:
        lines.append(f"- {point}")
    lines.append("")
    lines.append("## Open questions")
    lines.append("")
    for question in b.open_questions:
        lines.append(f"- {question}")
    lines.append("")
    lines.append("## Sources")
    lines.append("")
    if not b.results:
        lines.append("None.")
    else:
        for result in b.results:
            date_text = result.published.isoformat() if result.published else "date unknown"
            lines.append(f"- {result.title} ({date_text}): {result.url}")
    lines.append("")
    lines.append("Note: every development above comes from a Tavily search result. "
                 "Findings marked 'date unknown' had no published_date in the Tavily response; "
                 "their date could not be verified from Tavily alone.")
    return "\n".join(lines) + "\n"


def render_pdf(b: object, path: str) -> str:
    """Write the briefing as PDF with reportlab. Returns the path."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
    except ImportError as exc:
        raise RuntimeError(
            "reportlab is required for PDF output. Install it with: "
            "pip install -r requirements.txt"
        ) from exc

    styles = getSampleStyleSheet()
    story = []

    def para(text: str, style_name: str = "Normal"):
        story.append(Paragraph(html.escape(text), styles[style_name]))
        story.append(Spacer(1, 2 * mm))

    para(f"Pre-meeting briefing: {b.subject}", "Title")
    para(f"Meeting date: {b.meeting_date.isoformat()}")
    para(f"Search window: {b.window_start.isoformat()} to {b.window_end.isoformat()} (last 30 days)")
    para(f"Mode: {b.mode} | Summary mode: {b.summary_mode}")
    para(f"Results kept: {len(b.results)} | Dropped as too old: {b.dropped_old_count} | Dropped as duplicates: {b.dropped_duplicate_count}")
    if b.dropped_truncated_url_count or b.dropped_profile_count:
        para(f"Dropped as truncated URL: {b.dropped_truncated_url_count} | Dropped as profile page: {b.dropped_profile_count}")
    if b.source_note:
        para(b.source_note)
    enriched = getattr(b, "extract_enriched_count", 0)
    failed = getattr(b, "extract_failed_count", 0)
    if enriched or failed:
        para(
            f"Tavily Extract enriched {enriched} development(s) with "
            f"full content; {failed} URL(s) failed Extract and keep "
            "their search snippet as fallback. Dates and URLs are "
            "from the search result, never from Extract."
        )
    para("Summary", "Heading2")
    para(b.summary)
    excluded = getattr(b, "summary_excluded_count", 0)
    if excluded:
        para(
            f"Note: {excluded} kept development(s) below are not in the "
            "Top findings above, because the subject name does not appear "
            "in both their title and snippet. They are still listed in "
            "full, with source links, in Key developments."
        )
    para("Key developments", "Heading2")
    if not b.results:
        para("No verified developments in this window. Nothing is listed here on purpose.")
    else:
        for result in b.results:
            date_text = result.published.isoformat() if result.published else "date unknown"
            para(f"{result.title} ({date_text}) - Source: {result.url}")
            if result.snippet:
                para(result.snippet[:400])
            full = getattr(result, "full_content", "") or ""
            if full:
                para(f"Full content (Tavily Extract): {full[:800]}")
    para("Discussion points", "Heading2")
    for point in b.discussion_points:
        para(f"- {point}")
    para("Open questions", "Heading2")
    for question in b.open_questions:
        para(f"- {question}")
    para("Sources", "Heading2")
    if not b.results:
        para("None.")
    else:
        for result in b.results:
            date_text = result.published.isoformat() if result.published else "date unknown"
            para(f"{result.title} ({date_text}): {result.url}")

    doc = SimpleDocTemplate(path, pagesize=A4,
                            leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=18 * mm, bottomMargin=18 * mm,
                            title=f"Pre-meeting briefing: {b.subject}")
    doc.build(story)
    return path
