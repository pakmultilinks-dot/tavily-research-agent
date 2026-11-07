#!/usr/bin/env python3
"""Streamlit web UI for the Tavily Research Agent.

This is the second web UI, alongside the standard library web_ui.py.
Both reuse exactly the same tavily_agent pipeline, so a briefing
built here is identical to one built by the CLI for the same inputs.
The standard library UI still works without Streamlit; this UI is
optional and needs only `pip install streamlit` on top of
requirements.txt.

Run:
    streamlit run app.py
Then open the local URL Streamlit prints (usually
http://localhost:8501).

Live mode needs TAVILY_API_KEY in the environment. Tick "Mock mode"
to run with local fixtures instead. No key is ever written to disk
by this app.
"""
from __future__ import annotations

import sys
import tempfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    import streamlit as st
except ImportError as exc:  # clear message instead of a bare traceback
    raise RuntimeError(
        "Streamlit is not installed. Install it with: "
        "pip install streamlit"
    ) from exc

from main import load_fixtures
from tavily_agent.dates import meeting_window
from tavily_agent.render import render_markdown, render_pdf
from tavily_agent.tavily_client import search_all_categories
from tavily_agent.ui_helpers import (
    LIMITATION_NOTE,
    build_briefing_from_inputs,
    format_briefing_for_display,
    validate_inputs,
)


def main() -> None:
    st.set_page_config(page_title="Tavily Research Agent", layout="wide")
    st.title("Tavily Research Agent")
    st.write(
        "One-page briefing before a meeting, from the last 30 days only. "
        "Every development carries its source link."
    )

    subject = st.text_input("Company or person", placeholder="Acme Corp")
    meeting_value = st.date_input("Meeting date", value=date.today())
    mock = st.checkbox("Mock mode (local fixtures, no Tavily key needed)", value=False)
    max_results = st.slider("Max results per category", 1, 20, 5)
    search_depth = st.selectbox("Search depth", ["basic", "advanced"])

    if st.button("Build briefing"):
        clean_subject, meeting, error = validate_inputs(
            subject, meeting_value.isoformat() if meeting_value else ""
        )
        if error:
            st.error(error)
            return
        start, end = meeting_window(meeting)
        try:
            if mock:
                raw = load_fixtures("examples/fixtures.json", clean_subject)
                mode = "mock"
            else:
                raw = search_all_categories(
                    clean_subject, start.isoformat(), end.isoformat(),
                    max_results=max_results, search_depth=search_depth,
                )
                mode = "live"
        except Exception as exc:
            st.error(f"Search failed: {exc}")
            return
        briefing = build_briefing_from_inputs(
            clean_subject, meeting, raw, mode=mode
        )
        view = format_briefing_for_display(briefing)
        counts = view["counts"]

        st.subheader(f"Briefing: {view['subject']}")
        st.write(f"Meeting date: {view['meeting_date']} | Window: {view['window']}")
        st.write(f"Mode: {view['mode']} | Summary mode: {view['summary_mode']}")
        cols = st.columns(4)
        cols[0].metric("Kept", counts["kept"])
        cols[1].metric("Dropped as too old", counts["dropped_old"])
        cols[2].metric("Dropped as duplicates", counts["dropped_duplicates"])
        cols[3].metric("Not in summary", counts["summary_excluded"])
        if counts["dropped_truncated_url"] or counts["dropped_profile"]:
            st.write(
                f"Dropped as truncated URL: {counts['dropped_truncated_url']} | "
                f"Dropped as profile page: {counts['dropped_profile']}"
            )
        st.subheader("Summary")
        st.write(view["summary"])
        if counts["summary_excluded"]:
            st.info(
                f"{counts['summary_excluded']} kept development(s) below are "
                "not in the Top findings above, because the subject name "
                "does not appear in both their title and snippet. They are "
                "still listed in full, with source links."
            )
        if view["source_note"]:
            st.info(view["source_note"])
        st.info(LIMITATION_NOTE)

        st.subheader("Key developments")
        if not view["developments"]:
            st.write("No verified developments in this window. Nothing is listed here on purpose.")
        for dev in view["developments"]:
            st.markdown(f"**[{dev['title']}]({dev['url']})** ({dev['date']})")
            if dev["snippet"]:
                st.write(dev["snippet"][:400])

        st.subheader("Discussion points")
        for point in view["discussion_points"]:
            st.write(f"- {point}")
        st.subheader("Open questions")
        for question in view["open_questions"]:
            st.write(f"- {question}")

        md_text = render_markdown(briefing)
        st.download_button("Download briefing (Markdown)", md_text,
                           file_name="briefing.md", mime="text/markdown")
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = str(Path(tmp) / "briefing.pdf")
            render_pdf(briefing, pdf_path)
            pdf_bytes = Path(pdf_path).read_bytes()
        st.download_button("Download briefing (PDF)", pdf_bytes,
                           file_name="briefing.pdf", mime="application/pdf")


if __name__ == "__main__":
    main()
