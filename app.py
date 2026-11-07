#!/usr/bin/env python3
"""Streamlit web UI for the Tavily Research Agent.

This is the second web UI, alongside the standard library web_ui.py.
Both reuse exactly the same tavily_agent pipeline, so a briefing
built here is identical to one built by the CLI for the same inputs.
The standard library UI still works without Streamlit; this UI is
optional and needs only `pip install streamlit` on top of
requirements.txt (pinned to streamlit==1.67.0, verified on pip).

Modes, in order:
1. Demo (default): shows the three prebuilt live briefings from
   Nov 5, 2026 (OpenAI, Google, Microsoft). No Tavily call is
   made and no key is used, so the app always works, even on a
   public deployment. Demo data is from Nov 5, 2026.
2. Live: builds a fresh briefing with Tavily. It uses a visitor
   key entered in the app, for that session only, never stored
   and never written to a file. If the app is deployed with a
   key in Streamlit secrets, that is used only as a fallback
   when no visitor key is entered. Clear the key with the
   "Clear key" button when done.
3. Mock: runs with local fixtures, no key needed.

Run:
    streamlit run app.py
Then open the local URL Streamlit prints (usually
http://localhost:8501).

Deploy (Streamlit Community Cloud, owner step, not done here):
    1. Push this repo to GitHub.
    2. In the Streamlit workspace, click Create app, pick the
       repo, branch main, and app.py as the entry file, then
       click Deploy. Every push to main redeploys automatically.
    3. Secrets, if wanted: paste TAVILY_API_KEY into the app
       settings secrets, never into the repo. The file
       .streamlit/secrets.toml is ignored by git and must never
       be committed.
    4. Limits to expect: the app sleeps after 12 hours without
       traffic, so a first visit may show a wake-up screen.
       The demo link cannot be added to the locked HackCulture
       form, only to the README.
No key is ever written to disk by this app.
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
        "pip install -r requirements.txt"
    ) from exc

from main import load_fixtures
from tavily_agent.dates import meeting_window
from tavily_agent.demo import (
    DEMO_NOTE,
    clear_visitor_key,
    demo_companies,
    live_mode_available,
    load_demo_briefing,
    set_visitor_key,
)
from tavily_agent.render import render_markdown, render_pdf
from tavily_agent.tavily_client import AUTH_FIX_MESSAGE, search_all_categories
from tavily_agent.ui_helpers import (
    LIMITATION_NOTE,
    build_briefing_from_inputs,
    format_briefing_for_display,
    validate_inputs,
)


# Exact failure messages shown by this app. These are the only
# three failure cases the app reports, and the "What if it fails"
# section in demo mode quotes them verbatim. The 401 message
# comes from tavily_client.py; the app shows it prefixed with
# "Search failed: " when a live search raises it.
NO_KEY_MESSAGE = "Live mode needs a Tavily key. Enter your own key above."
NO_RESULTS_MESSAGE = (
    "No verified developments in this window. Nothing is listed here on purpose."
)


def _show_briefing(briefing) -> None:
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
        st.write(NO_RESULTS_MESSAGE)
    for dev in view["developments"]:
        st.markdown(f"**[{dev['title']}]({dev['url']})** ({dev['date']})")
        if dev["snippet"]:
            st.write(dev["snippet"][:400])
        if dev.get("full_content"):
            st.write(f"Full content (Tavily Extract): {dev['full_content'][:800]}")

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


def main() -> None:
    st.set_page_config(page_title="Tavily Research Agent", layout="wide")
    st.title("Tavily Research Agent")
    st.write(
        "One-page briefing before a meeting, from the last 30 days only. "
        "Every development carries its source link."
    )

    mode = st.radio(
        "Mode",
        ["Demo (prebuilt live briefings)", "Live (your own Tavily key)", "Mock (fixtures)"],
        index=0,
    )

    if mode.startswith("Demo"):
        st.info(DEMO_NOTE)
        st.write(
            "30-second demo: 1. You are in Demo mode already, no key needed. "
            "2. Pick a company below. 3. Read the summary, then open one source link."
        )
        company_names = [name for name, _ in demo_companies()]
        chosen = st.selectbox("Company", company_names, index=0)
        slug = dict(demo_companies())[chosen]
        demo = load_demo_briefing(slug)
        st.subheader(f"Briefing: {demo['company']}")
        st.write(
            f"Meeting date: {demo['meeting_date']} | Window: {demo['window']} | "
            f"Results kept: {demo['kept']}"
        )
        st.markdown(demo["markdown"])
        st.download_button("Download briefing (Markdown)", demo["markdown"],
                           file_name=f"briefing-{slug}.md", mime="text/markdown")
        if demo["pdf_exists"]:
            st.download_button("Download briefing (PDF)",
                               demo["pdf_path"].read_bytes(),
                               file_name=f"briefing-{slug}.pdf",
                               mime="application/pdf")
        st.subheader("What if it fails")
        st.write("Three honest failure cases, with the exact message you will see:")
        st.write(f"- No key: {NO_KEY_MESSAGE}")
        st.write(f"- Wrong key: Search failed: {AUTH_FIX_MESSAGE}")
        st.write(f"- No results: {NO_RESULTS_MESSAGE}")
        st.write("For a fresh briefing, switch to Live mode and enter your own Tavily key.")
        return

    subject = st.text_input("Company or person", placeholder="Acme Corp")
    meeting_value = st.date_input("Meeting date", value=date.today())
    max_results = st.slider("Max results per category", 1, 20, 5)
    search_depth = st.selectbox("Search depth", ["basic", "advanced"])

    if mode.startswith("Live"):
        visitor_key = st.text_input(
            "Your Tavily key (used for this session only, never stored)",
            type="password",
        )
        secrets_key = None
        try:
            secrets_key = st.secrets.get("TAVILY_API_KEY")
        except Exception:
            secrets_key = None
        available, source = live_mode_available(visitor_key, secrets_key)
        if visitor_key:
            set_visitor_key(visitor_key)
        elif source == "secrets":
            # Deployment secret, used only as a fallback in memory.
            set_visitor_key(secrets_key)
        if st.button("Clear key"):
            clear_visitor_key()
            st.info("Key cleared from this session.")
        if not available:
            st.warning(
                "Live mode needs a Tavily key. Enter your own key above, "
                "or run the app with a key in Streamlit secrets. "
                "Demo mode needs no key."
            )

    if st.button("Build briefing"):
        clean_subject, meeting, error = validate_inputs(
            subject, meeting_value.isoformat() if meeting_value else ""
        )
        if error:
            st.error(error)
            return
        start, end = meeting_window(meeting)
        try:
            if mode.startswith("Mock"):
                raw = load_fixtures("examples/fixtures.json", clean_subject)
                briefing_mode = "mock"
            else:
                available, _source = live_mode_available(
                    visitor_key if mode.startswith("Live") else None,
                    secrets_key if mode.startswith("Live") else None,
                )
                if not available:
                    st.error(NO_KEY_MESSAGE)
                    return
                raw = search_all_categories(
                    clean_subject, start.isoformat(), end.isoformat(),
                    max_results=max_results, search_depth=search_depth,
                )
                briefing_mode = "live"
        except Exception as exc:
            st.error(f"Search failed: {exc}")
            return
        briefing = build_briefing_from_inputs(
            clean_subject, meeting, raw, mode=briefing_mode
        )
        _show_briefing(briefing)


if __name__ == "__main__":
    main()
