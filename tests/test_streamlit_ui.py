"""Unit tests for the Streamlit UI helpers and the relevance-aware summary.

Run from the repo root:
    python3 -m unittest discover -s tests -v

All tests are offline. No Tavily key and no network are needed.
The app.py import test is skipped when Streamlit is not installed,
because Streamlit is an optional dependency.
"""
import importlib.util
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tavily_agent.briefing import (
    build_briefing,
    mentions_subject,
    summary_eligible_results,
)
from tavily_agent.models import SearchResult
from tavily_agent.render import render_markdown
from tavily_agent.summarizer import extractive_summary
from tavily_agent.ui_helpers import (
    briefing_counts,
    format_briefing_for_display,
    validate_inputs,
)


def raw(title, url, published, category="news", score=0.9, snippet="Test snippet."):
    return {"title": title, "url": url, "snippet": snippet,
            "published": published, "score": score, "category": category}


def result(title, snippet, subject_date=date(2026, 11, 3)):
    return SearchResult(title=title, url="https://example.com/x",
                        snippet=snippet, published=subject_date)


class TestMentionsSubject(unittest.TestCase):
    def test_needs_both_title_and_snippet(self):
        self.assertTrue(mentions_subject(
            result("Google launches Gemini", "Google launched a new agent."), "Google"))
        self.assertFalse(mentions_subject(
            result("Google launches Gemini", "A new agent was launched."), "Google"))
        self.assertFalse(mentions_subject(
            result("A new agent launches", "Google launched a new agent."), "Google"))
        self.assertFalse(mentions_subject(
            result("A new agent launches", "A new agent was launched."), "Google"))

    def test_case_insensitive_and_no_short_forms(self):
        self.assertTrue(mentions_subject(
            result("GOOGLE NEWS", "google news today."), "Google"))
        # Alphabet is the parent company, not the subject string,
        # so it does not count as a mention of Google.
        self.assertFalse(mentions_subject(
            result("Alphabet president on funding", "Alphabet is spending."), "Google"))

    def test_summary_eligible_filters_the_pool(self):
        pool = [
            result("Google launches Gemini", "Google launched a new agent."),
            result("Google news", "A crash happened somewhere else."),
        ]
        eligible = summary_eligible_results(pool, "Google")
        self.assertEqual(len(eligible), 1)
        self.assertIn("Gemini", eligible[0].title)


class TestRelevanceAwareSummary(unittest.TestCase):
    def test_learjet_snippet_leaves_the_google_summary(self):
        briefing = build_briefing(
            "Google", date(2026, 11, 5),
            [
                raw("Google will cut off search access for students",
                    "https://example.com/google-schools", date(2026, 11, 3),
                    snippet="Parents and 2 young children among victims of Learjet crash in Florida, family says."),
                raw("Google launches Gemini AI workplace agent",
                    "https://example.com/google-gemini", date(2026, 10, 8),
                    snippet="Google launches Gemini AI workplace agent that can write code and run tasks."),
            ],
            mode="mock", today=date(2026, 11, 5))
        self.assertEqual(len(briefing.results), 2)
        self.assertEqual(briefing.summary_excluded_count, 1)
        self.assertNotIn("Learjet", briefing.summary)
        self.assertIn("Gemini", briefing.summary)
        md = render_markdown(briefing)
        # The excluded development stays in Key developments in full.
        self.assertIn("https://example.com/google-schools", md)
        self.assertIn("Learjet", md)
        self.assertIn("1 kept development(s) below are not in the Top findings", md)

    def test_openai_hires_article_leaves_the_microsoft_summary(self):
        briefing = build_briefing(
            "Microsoft", date(2026, 11, 5),
            [
                raw("OpenAI hones public sector focus with new leadership hires",
                    "https://example.com/openai-hires", date(2026, 11, 4),
                    snippet="Peter Guerra will serve as OpenAI head of tech success."),
                raw("Microsoft plans to raise $25 billion in debt",
                    "https://example.com/microsoft-debt", date(2026, 10, 30),
                    snippet="Microsoft will access additional funding sources to complement its own cash flow."),
            ],
            mode="mock", today=date(2026, 11, 5))
        self.assertEqual(len(briefing.results), 2)
        self.assertEqual(briefing.summary_excluded_count, 1)
        self.assertNotIn("OpenAI", briefing.summary)
        self.assertIn("Microsoft will access additional funding", briefing.summary)

    def test_extractive_summary_uses_subject_when_given(self):
        pool = [
            result("Google news", "A crash happened somewhere else."),
            result("Google launches Gemini", "Google launched a new agent."),
        ]
        self.assertNotIn("crash", extractive_summary(pool, subject="Google"))
        # The summary quotes the snippet, not the title, so the
        # eligible finding appears as its snippet sentence.
        self.assertIn("Google launched a new agent.", extractive_summary(pool, subject="Google"))
        # Without a subject, the previous behaviour is kept.
        self.assertIn("crash", extractive_summary(pool))


class TestUiHelpers(unittest.TestCase):
    def test_validate_inputs_accepts_valid_input(self):
        subject, meeting, error = validate_inputs("Acme Corp", "2026-11-10")
        self.assertIsNone(error)
        self.assertEqual(subject, "Acme Corp")
        self.assertEqual(meeting, date(2026, 11, 10))

    def test_validate_inputs_rejects_empty_subject_and_bad_date(self):
        _, _, error = validate_inputs("   ", "2026-11-10")
        self.assertIn("required", error)
        _, _, error = validate_inputs("Acme Corp", "")
        self.assertIn("required", error)
        _, _, error = validate_inputs("Acme Corp", "10 Nov 2026")
        self.assertIn("YYYY-MM-DD", error)

    def test_format_briefing_for_display_keeps_urls_and_counts(self):
        briefing = build_briefing(
            "Example Company", date(2026, 11, 10),
            [raw("Example Company launches a product",
                 "https://example.com/launch", date(2026, 11, 2),
                 category="launches",
                 snippet="Example Company launched a new product.")],
            mode="mock", today=date(2026, 11, 10))
        view = format_briefing_for_display(briefing)
        self.assertEqual(view["subject"], "Example Company")
        self.assertEqual(view["counts"]["kept"], 1)
        self.assertEqual(view["developments"][0]["url"], "https://example.com/launch")
        self.assertEqual(view["developments"][0]["date"], "2026-11-02")
        self.assertIn("401", view["limitation_note"])
        counts = briefing_counts(briefing)
        self.assertEqual(counts["kept"], 1)
        self.assertEqual(counts["summary_excluded"], 0)


@unittest.skipUnless(importlib.util.find_spec("streamlit") is not None,
                     "Streamlit is not installed (optional dependency)")
class TestStreamlitAppImport(unittest.TestCase):
    def test_app_imports_cleanly(self):
        import app  # noqa: F401  (import only, the UI runs under main())
        self.assertTrue(hasattr(app, "main"))

    def test_app_uses_the_shared_pipeline(self):
        import app
        import inspect
        source = inspect.getsource(app)
        self.assertIn("build_briefing_from_inputs", source)
        self.assertIn("format_briefing_for_display", source)
        self.assertIn("validate_inputs", source)


if __name__ == "__main__":
    unittest.main()
