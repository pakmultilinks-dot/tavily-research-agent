"""Unit tests for the Tavily Research Agent briefing pipeline.

Run from the repo root:
    python3 -m unittest discover -s tests -v

All tests are offline. No Tavily key and no network are needed.
"""
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tavily_agent.briefing import build_briefing, filter_and_dedupe
from tavily_agent.dates import in_window, meeting_window, parse_published_date
from tavily_agent.render import render_markdown


def raw(title, url, published, category="news", score=0.9, snippet="Test snippet."):
    return {"title": title, "url": url, "snippet": snippet,
            "published": published, "score": score, "category": category}


class TestDates(unittest.TestCase):
    def test_parse_iso_date(self):
        self.assertEqual(parse_published_date("2026-10-20"), date(2026, 10, 20))

    def test_parse_rfc_gmt_date_from_official_example(self):
        self.assertEqual(parse_published_date("Tue, 11 Mar 2025 17:00:00 GMT"),
                         date(2025, 3, 11))

    def test_parse_none_and_garbage_returns_none(self):
        self.assertIsNone(parse_published_date(None))
        self.assertIsNone(parse_published_date(""))
        self.assertIsNone(parse_published_date("not a date"))

    def test_meeting_window_caps_future_meeting_at_today(self):
        start, end = meeting_window(date(2027, 1, 1), today=date(2026, 11, 3))
        self.assertEqual(end, date(2026, 11, 3))
        self.assertEqual(start, date(2026, 10, 4))

    def test_in_window_boundaries(self):
        start, end = date(2026, 10, 11), date(2026, 11, 10)
        self.assertTrue(in_window(date(2026, 10, 11), start, end))
        self.assertTrue(in_window(date(2026, 11, 10), start, end))
        self.assertFalse(in_window(date(2026, 10, 10), start, end))
        self.assertFalse(in_window(None, start, end))


class TestFiltering(unittest.TestCase):
    def test_old_results_dropped_recent_kept(self):
        start, end = date(2026, 10, 11), date(2026, 11, 10)
        kept, dropped_old, _ = filter_and_dedupe([
            raw("Recent", "https://example.com/recent", date(2026, 11, 2)),
            raw("Old", "https://example.com/old", date(2026, 8, 15)),
        ], start, end)
        self.assertEqual([r.title for r in kept], ["Recent"])
        self.assertEqual(dropped_old, 1)

    def test_duplicates_deduplicated_by_normalised_url(self):
        start, end = date(2026, 10, 11), date(2026, 11, 10)
        kept, _, dropped_dup = filter_and_dedupe([
            raw("Launch", "https://example.com/news/launch", date(2026, 11, 2), score=0.9),
            raw("Launch copy", "https://www.example.com/news/launch/", date(2026, 11, 2), score=0.8),
        ], start, end)
        self.assertEqual(len(kept), 1)
        self.assertEqual(dropped_dup, 1)
        self.assertEqual(kept[0].score, 0.9)

    def test_undated_kept_but_flagged(self):
        start, end = date(2026, 10, 11), date(2026, 11, 10)
        kept, _, _ = filter_and_dedupe([
            raw("Undated", "https://example.com/undated", None),
        ], start, end)
        self.assertEqual(len(kept), 1)
        self.assertTrue(kept[0].date_unknown)

    def test_newest_first_undated_last(self):
        start, end = date(2026, 10, 11), date(2026, 11, 10)
        kept, _, _ = filter_and_dedupe([
            raw("Undated", "https://example.com/u", None),
            raw("Older", "https://example.com/older", date(2026, 10, 20)),
            raw("Newer", "https://example.com/newer", date(2026, 11, 2)),
        ], start, end)
        self.assertEqual([r.title for r in kept], ["Newer", "Older", "Undated"])


class TestBriefing(unittest.TestCase):
    def test_briefing_lists_every_development_with_its_url(self):
        briefing = build_briefing(
            "Example Company", date(2026, 11, 10),
            [raw("Launch", "https://example.com/launch", date(2026, 11, 2),
                 category="launches")],
            mode="mock", today=date(2026, 11, 10))
        md = render_markdown(briefing)
        self.assertIn("https://example.com/launch", md)
        self.assertIn("2026-11-02", md)
        self.assertGreaterEqual(len(briefing.discussion_points), 1)
        self.assertLessEqual(len(briefing.discussion_points), 5)
        self.assertGreaterEqual(len(briefing.open_questions), 1)
        self.assertLessEqual(len(briefing.open_questions), 5)

    def test_empty_results_briefing_invents_nothing(self):
        briefing = build_briefing("Nobody Corp", date(2026, 11, 10), [],
                                  mode="mock", today=date(2026, 11, 10))
        md = render_markdown(briefing)
        self.assertIn("No verified developments", md)
        self.assertIn("No results were found", briefing.summary)
        self.assertEqual(len(briefing.results), 0)

    def test_fixture_pipeline_end_to_end(self):
        # Uses the repo fixtures file, with a fixed 'today' so the
        # window is stable regardless of when tests run.
        import json
        fixtures = json.loads(
            (Path(__file__).resolve().parents[1] / "examples" / "fixtures.json").read_text())
        raw_results = [{
            "title": r["title"], "url": r["url"],
            "snippet": r["content"],
            "published": parse_published_date(r.get("published_date")),
            "score": r["score"], "category": r["category"],
        } for r in fixtures["results"]]
        briefing = build_briefing("Example Company", date(2026, 11, 10),
                                  raw_results, mode="mock",
                                  today=date(2026, 11, 10))
        # 6 fixture rows: 1 old dropped, 1 duplicate dropped, 4 kept.
        self.assertEqual(len(briefing.results), 4)
        self.assertEqual(briefing.dropped_old_count, 1)
        self.assertEqual(briefing.dropped_duplicate_count, 1)
        titles = [r.title for r in briefing.results]
        self.assertNotIn("Example Company in older news from August", titles)


if __name__ == "__main__":
    unittest.main()
