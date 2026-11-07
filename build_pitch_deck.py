#!/usr/bin/env python3
"""Rebuild the pitch deck (PDF and PPTX) from one slide list.

Run:
    python3 build_pitch_deck.py

Writes pitch-deck.pdf (reportlab) and pitch-deck.pptx (python-pptx),
10 slides each, same text in both. The submitted HackCulture deck
file is locked and is not changed by this script; this rebuilds the
deck in the public repo so judges clicking the repo link see the
current state.

Keep the text in SLIDES as the single source of truth. Do not add
claims that are not in README.md or STATUS.md.
"""
from __future__ import annotations

from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent

SLIDES = [
    (
        "Tavily Research Agent",
        "Pre-meeting briefings from the last 30 days, with sources you can check",
        [
            "Geek Room Global AI Hackathon",
            "Theme: Tavily Research Agent (Tavily-primary)",
            "November 2026",
            "A real, runnable Python app: CLI plus web UI, Markdown and PDF output",
        ],
    ),
    (
        "1. Problem: meetings start cold",
        "Before an important meeting, you need the last 30 days, fast",
        [
            "What did the company do lately: news, launches, hires, funding?",
            "Manual search is slow, and it is easy to miss the one update that matters.",
            "Plain AI answers mix old and new information, with no sources to check.",
            "So people walk into sales, hiring, partnership, and investor meetings unprepared.",
        ],
    ),
    (
        "2. Solution: one page, in seconds",
        "Type a name and a meeting date, get a briefing you can trust",
        [
            "A short summary of the last 30 days.",
            "Key developments, each with a date and a source link.",
            "3 to 5 discussion points and 3 to 5 open questions.",
            "No invented facts: every development comes from a Tavily result and carries its source URL.",
            "No results? The briefing says so clearly and lists nothing.",
        ],
    ),
    (
        "3. Demo flow: what judges will see",
        "Four searches, one briefing, every source clickable",
        [
            "1. Open the CLI, the standard library web UI, or the Streamlit web UI.",
            "2. Enter a real company name and a meeting date.",
            "3. Four Tavily searches run: news, launches, hires, funding.",
            "4. Briefing appears: newest first, duplicates removed, old results dropped.",
            "5. Open one source link to prove it is real.",
            "6. Markdown and PDF exports, same content in both.",
        ],
    ),
    (
        "4. Technical architecture",
        "A small pipeline with the 30-day rule enforced twice",
        [
            "Input: CLI, Python standard-library web UI, or Streamlit web UI (app.py), all one pipeline.",
            "Tavily Search API: POST api.tavily.com/search, Bearer auth, topic news, time_range month, start_date and end_date for the 30-day window.",
            "Parse published_date (ISO and RFC/GMT), filter outside the window, deduplicate by normalised URL, sort newest first, undated flagged.",
            "Summarise: relevance-aware extractive by default, optional LLM. Render: Markdown and PDF.",
            "Key is never hardcoded: Tavily key comes only from TAVILY_API_KEY.",
        ],
    ),
    (
        "5. Live proof: real Tavily data, Nov 5, 2026",
        "12 searches, 60 results, 37 kept, every kept item sourced",
        [
            "Meeting date 2026-11-05, window 2026-10-06 to 2026-11-05.",
            "OpenAI: 14 kept of 20. Google: 15 kept of 20. Microsoft: 8 kept of 20.",
            "Dropped 23: 16 truncated URL, 5 profile pages, 2 duplicates, 0 too old.",
            "Files: examples/live-openai/, examples/live-google/, examples/live-microsoft/, briefing.md and briefing.pdf in each, plus the source JSON.",
            "Tests: 23 run, 23 passed (offline unit tests).",
        ],
    ),
    (
        "6. Live findings, from the kept results",
        "Real headlines, real dates, real links in the briefings",
        [
            "OpenAI: to acquire Pierre Computer Company, Nov 4, 2026.",
            "OpenAI: GPT-6 and Intelligent UI in ChatGPT, Oct 8, 2026.",
            "Google: Gemini AI workplace agent that can write code and run tasks, Oct 8, 2026.",
            "Google: universal online shopping cart ahead of the holidays, Oct 15, 2026.",
            "Microsoft: buyouts to 60,000 workers as it pours money into AI, Oct 26, 2026.",
            "Microsoft: plans to raise $25 billion in debt for the AI buildout, Oct 30, 2026.",
        ],
    ),
    (
        "7. How AI is used",
        "Tavily does the research, the summary cannot invent facts",
        [
            "Tavily Search is the research layer: real-time results, ranked, with snippets.",
            "Summarisation is extractive by default: the summary reuses the first sentences of the top result snippets and counts results by category.",
            "The summary is relevance-aware: only developments that name the subject in both title and snippet are quoted in the Top findings. Other kept developments stay listed in full, with source links.",
            "An LLM summary is used only if LLM_API_KEY is set, only on supplied snippets, told not to invent dates, facts, or sources, with fallback to extractive.",
            "The briefing labels which mode was used (extractive or llm).",
            "The LLM is never used to add new developments.",
        ],
    ),
    (
        "8. Impact and scalability",
        "One briefing per meeting, for any company or person",
        [
            "Saves preparation time before every sales, hiring, partnership, or investor meeting.",
            "Works for any company or person with public web coverage.",
            "Scales by adding categories, languages, or export formats, without changing the core filter and sourcing rules.",
            "Cost is bounded: 4 searches per briefing, basic depth by default, no raw content fetched.",
        ],
    ),
    (
        "9. Limitations, next steps, and why this wins",
        "Finished, working, and honest",
        [
            "Playground snippets are truncated at about 100 characters, kept exactly as returned.",
            "The direct API route is still unproven: HTTP 401 here, while the same key works in the Playground. The live briefings prove the pipeline on real Tavily data.",
            "Submitted for evaluation Nov 5, 2026, Under Review. The repo stays open for improvements until judging on Nov 29, 2026.",
            "Judges can run it and check every source in the live briefings.",
            "The 30-day rule is enforced in code and in tests, not just in words.",
            "Tavily Research Agent: know what happened, before you walk in.",
        ],
    ),
]


def build_pdf(path: Path) -> None:
    from reportlab.lib.pagesizes import landscape, A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, PageBreak
    from reportlab.lib.enums import TA_LEFT
    import html

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("DeckTitle", parent=styles["Title"], fontSize=28, leading=32, alignment=TA_LEFT)
    sub_style = ParagraphStyle("DeckSub", parent=styles["Heading2"], fontSize=15, leading=19, alignment=TA_LEFT)
    body_style = ParagraphStyle("DeckBody", parent=styles["Normal"], fontSize=13, leading=18, alignment=TA_LEFT)
    foot_style = ParagraphStyle("DeckFoot", parent=styles["Normal"], fontSize=10, leading=13, alignment=TA_LEFT)
    story = []
    total = len(SLIDES)
    for index, (title, subtitle, bullets) in enumerate(SLIDES, start=1):
        story.append(Paragraph(html.escape(title), title_style))
        story.append(Spacer(1, 4 * mm))
        story.append(Paragraph(html.escape(subtitle), sub_style))
        story.append(Spacer(1, 6 * mm))
        for bullet in bullets:
            story.append(Paragraph(html.escape(bullet), body_style))
            story.append(Spacer(1, 3 * mm))
        story.append(Spacer(1, 6 * mm))
        story.append(Paragraph(f"{index} / {total}", foot_style))
        if index < total:
            story.append(PageBreak())
    doc = SimpleDocTemplate(str(path), pagesize=landscape(A4),
                            leftMargin=20 * mm, rightMargin=20 * mm,
                            topMargin=18 * mm, bottomMargin=18 * mm,
                            title="Tavily Research Agent - Pitch Deck")
    doc.build(story)


def build_pptx(path: Path) -> None:
    from pptx import Presentation
    from pptx.util import Inches, Pt

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]
    total = len(SLIDES)
    for index, (title, subtitle, bullets) in enumerate(SLIDES, start=1):
        slide = prs.slides.add_slide(blank)
        title_box = slide.shapes.add_textbox(Inches(0.6), Inches(0.4), Inches(12.1), Inches(1.0))
        title_frame = title_box.text_frame
        title_frame.word_wrap = True
        title_frame.paragraphs[0].text = title
        title_frame.paragraphs[0].font.size = Pt(32)
        title_frame.paragraphs[0].font.bold = True
        sub_box = slide.shapes.add_textbox(Inches(0.6), Inches(1.4), Inches(12.1), Inches(0.6))
        sub_frame = sub_box.text_frame
        sub_frame.word_wrap = True
        sub_frame.paragraphs[0].text = subtitle
        sub_frame.paragraphs[0].font.size = Pt(18)
        body_box = slide.shapes.add_textbox(Inches(0.6), Inches(2.2), Inches(12.1), Inches(4.4))
        body_frame = body_box.text_frame
        body_frame.word_wrap = True
        for i, bullet in enumerate(bullets):
            para = body_frame.paragraphs[0] if i == 0 else body_frame.add_paragraph()
            para.text = bullet
            para.font.size = Pt(16)
            para.space_after = Pt(10)
        foot_box = slide.shapes.add_textbox(Inches(0.6), Inches(6.9), Inches(12.1), Inches(0.4))
        foot_frame = foot_box.text_frame
        foot_frame.word_wrap = True
        foot_frame.paragraphs[0].text = f"{index} / {total}"
        foot_frame.paragraphs[0].font.size = Pt(12)
    prs.save(str(path))


def main() -> int:
    build_pdf(PROJECT_DIR / "pitch-deck.pdf")
    build_pptx(PROJECT_DIR / "pitch-deck.pptx")
    print(f"Built pitch-deck.pdf and pitch-deck.pptx, {len(SLIDES)} slides each")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
