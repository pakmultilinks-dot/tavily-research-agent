"""Unit tests for demo mode and the visitor-key live mode.

Run from the repo root:
    python3 -m unittest discover -s tests -v

All tests are offline. No Tavily key and no network are needed,
and no Streamlit import is needed: the demo helpers live in
tavily_agent/demo.py, which is framework-free. The fake key
below is an invented test string.
"""
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tavily_agent.demo import (
    clear_visitor_key,
    demo_companies,
    live_mode_available,
    load_demo_briefing,
    set_visitor_key,
)

REPO = Path(__file__).resolve().parents[1]


class TestDemoBriefings(unittest.TestCase):
    def test_demo_lists_all_three_live_companies(self):
        companies = demo_companies()
        self.assertEqual([name for name, _ in companies],
                         ["OpenAI", "Google", "Microsoft"])
        self.assertEqual([slug for _, slug in companies],
                         ["openai", "google", "microsoft"])

    def test_demo_kept_counts_match_the_live_briefings(self):
        self.assertEqual(load_demo_briefing("openai")["kept"], 14)
        self.assertEqual(load_demo_briefing("google")["kept"], 15)
        self.assertEqual(load_demo_briefing("microsoft")["kept"], 8)

    def test_demo_markdown_is_the_committed_live_briefing(self):
        demo = load_demo_briefing("openai")
        self.assertEqual(demo["company"], "OpenAI")
        self.assertEqual(demo["meeting_date"], "2026-11-05")
        self.assertIn("LIVE via Tavily Playground", demo["markdown"])
        self.assertTrue(demo["pdf_exists"])
        self.assertTrue(demo["pdf_path"].exists())

    def test_demo_unknown_slug_is_rejected(self):
        with self.assertRaises(ValueError):
            load_demo_briefing("acme")


class TestLiveModeAvailability(unittest.TestCase):
    def test_no_key_means_live_mode_is_disabled(self):
        self.assertEqual(live_mode_available(None, None), (False, None))
        self.assertEqual(live_mode_available("   ", None), (False, None))
        self.assertEqual(live_mode_available("", ""), (False, None))

    def test_visitor_key_enables_live_mode_as_visitor(self):
        self.assertEqual(live_mode_available("visitor-key", None),
                         (True, "visitor"))

    def test_secrets_key_is_only_a_fallback(self):
        self.assertEqual(live_mode_available(None, "secrets-key"),
                         (True, "secrets"))
        # A visitor key wins over a deployment secret.
        self.assertEqual(live_mode_available("visitor-key", "secrets-key"),
                         (True, "visitor"))


class TestVisitorKeyHandling(unittest.TestCase):
    def test_visitor_key_is_kept_in_memory_only_and_cleared(self):
        with self.subTest("set trims and stores in memory"):
            set_visitor_key("  tvly-testkey-123  ")
            self.assertEqual(os.environ.get("TAVILY_API_KEY"), "tvly-testkey-123")
        with self.subTest("clear removes it"):
            clear_visitor_key()
            self.assertNotIn("TAVILY_API_KEY", os.environ)
        with self.subTest("no secrets file was created"):
            self.assertFalse((REPO / ".streamlit" / "secrets.toml").exists())


if __name__ == "__main__":
    unittest.main()
