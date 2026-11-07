"""Unit tests for the Tavily Extract client.

Run from the repo root:
    python3 -m unittest discover -s tests -v

All tests are offline. The HTTP layer is mocked with
unittest.mock, so no Tavily key and no network are needed.
No test here makes a live call, and no key value is written
to any file. The fake key below is an invented test string.
"""
import os
import subprocess
import sys
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tavily_agent.extract import (
    enrich_top_results,
    extract_batch,
    extract_for_urls,
)
from tavily_agent.models import SearchResult
from tavily_agent.tavily_client import TavilyAuthError

FAKE_KEY = "tvly-testkey-123"
REPO = Path(__file__).resolve().parents[1]


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


def ok_payload():
    return {
        "results": [
            {"url": "https://example.com/a",
             "raw_content": "First chunk text here. chunk 2 Second chunk text."},
            {"url": "https://example.com/b",
             "raw_content": "Only one chunk of content."},
        ],
        "failed_results": [{"url": "https://example.com/c"}],
        "response_time": 1.2,
    }


class TestExtractBatch(unittest.TestCase):
    def test_mocked_200_reads_results_and_failed_results(self):
        with patch("tavily_agent.extract.requests.post",
                   return_value=FakeResponse(200, ok_payload())):
            outcome = extract_batch(
                ["https://example.com/a", "https://example.com/b",
                 "https://example.com/c"],
                query="OpenAI news", api_key=FAKE_KEY)
        # First chunk only: text before the chunk 2 marker.
        self.assertEqual(outcome["extracted"]["https://example.com/a"],
                         "First chunk text here.")
        self.assertEqual(outcome["extracted"]["https://example.com/b"],
                         "Only one chunk of content.")
        self.assertIn("https://example.com/c", outcome["failed"])
        # A URL in neither array would also land in failed; here
        # every URL is accounted for, so failed has exactly one.
        self.assertEqual(len(outcome["failed"]), 1)

    def test_url_with_no_content_lands_in_failed(self):
        payload = {"results": [{"url": "https://example.com/a", "raw_content": ""}],
                   "failed_results": []}
        with patch("tavily_agent.extract.requests.post",
                   return_value=FakeResponse(200, payload)):
            outcome = extract_batch(["https://example.com/a"], api_key=FAKE_KEY)
        self.assertEqual(outcome["extracted"], {})
        self.assertIn("https://example.com/a", outcome["failed"])

    def test_mocked_401_raises_auth_error_and_falls_back(self):
        with patch("tavily_agent.extract.requests.post",
                   return_value=FakeResponse(401, {})):
            with self.assertRaises(TavilyAuthError) as ctx:
                extract_batch(["https://example.com/a"], api_key=FAKE_KEY)
        self.assertIn("app.tavily.com", str(ctx.exception))
        self.assertNotIn(FAKE_KEY, str(ctx.exception))

    def test_chunks_per_source_is_capped_at_5(self):
        with self.assertRaises(ValueError):
            extract_batch(["https://example.com/a"], chunks_per_source=6,
                          api_key=FAKE_KEY)
        with self.assertRaises(ValueError):
            extract_batch(["https://example.com/a"], chunks_per_source=0,
                          api_key=FAKE_KEY)

    def test_chunks_per_source_sent_only_with_a_query(self):
        with patch("tavily_agent.extract.requests.post",
                   return_value=FakeResponse(200, {"results": []})) as mock_post:
            extract_batch(["https://example.com/a"], api_key=FAKE_KEY)
            payload = mock_post.call_args.kwargs["json"]
            self.assertNotIn("chunks_per_source", payload)
            self.assertNotIn("query", payload)
        with patch("tavily_agent.extract.requests.post",
                   return_value=FakeResponse(200, {"results": []})) as mock_post:
            extract_batch(["https://example.com/a"], query="OpenAI news",
                          chunks_per_source=3, api_key=FAKE_KEY)
            payload = mock_post.call_args.kwargs["json"]
            self.assertEqual(payload["chunks_per_source"], 3)
            self.assertEqual(payload["query"], "OpenAI news")

    def test_more_than_20_urls_is_rejected(self):
        with self.assertRaises(ValueError):
            extract_batch([f"https://example.com/{i}" for i in range(21)],
                          api_key=FAKE_KEY)


class TestExtractBatching(unittest.TestCase):
    def test_25_urls_are_sent_in_batches_of_20(self):
        urls = [f"https://example.com/{i}" for i in range(25)]
        with patch("tavily_agent.extract.requests.post",
                   return_value=FakeResponse(200, {"results": []})) as mock_post:
            outcome = extract_for_urls(urls, api_key=FAKE_KEY)
        self.assertEqual(mock_post.call_count, 2)
        first_batch = mock_post.call_args_list[0].kwargs["json"]["urls"]
        second_batch = mock_post.call_args_list[1].kwargs["json"]["urls"]
        self.assertEqual(len(first_batch), 20)
        self.assertEqual(len(second_batch), 5)
        self.assertEqual(len(outcome["failed"]), 25)


class TestEnrichTopResults(unittest.TestCase):
    def _result(self, url, title="Title"):
        return SearchResult(
            title=title, url=url, snippet="Short snippet.",
            published=date(2026, 11, 3), score=0.9, category="news")

    def test_enrich_attaches_full_content_and_keeps_date_and_snippet(self):
        results = [self._result("https://example.com/a"),
                   self._result("https://example.com/b")]
        fake = {"extracted": {"https://example.com/a": "Full first paragraph."},
                "failed": ["https://example.com/b"]}
        with patch("tavily_agent.extract.extract_for_urls", return_value=fake):
            outcome = enrich_top_results(results, "OpenAI", top_n=8,
                                         api_key=FAKE_KEY)
        self.assertEqual(outcome, {"enriched": 1, "failed": 1})
        self.assertEqual(results[0].full_content, "Full first paragraph.")
        self.assertEqual(results[0].snippet, "Short snippet.")
        self.assertEqual(results[0].published.isoformat(), "2026-11-03")
        self.assertEqual(results[0].url, "https://example.com/a")
        self.assertEqual(results[1].full_content, "")

    def test_enrich_only_touches_the_top_8(self):
        results = [self._result(f"https://example.com/{i}") for i in range(10)]
        with patch("tavily_agent.extract.extract_for_urls",
                   return_value={"extracted": {}, "failed": []}) as mock_extract:
            enrich_top_results(results, "OpenAI", top_n=8, api_key=FAKE_KEY)
            sent = mock_extract.call_args.args[0]
        self.assertEqual(len(sent), 8)

    def test_enrich_with_top_n_zero_makes_no_call(self):
        results = [self._result("https://example.com/a")]
        with patch("tavily_agent.extract.extract_for_urls") as mock_extract:
            outcome = enrich_top_results(results, "OpenAI", top_n=0,
                                         api_key=FAKE_KEY)
        self.assertEqual(outcome, {"enriched": 0, "failed": 0})
        mock_extract.assert_not_called()


class TestEnrichFlagDefault(unittest.TestCase):
    def test_builder_exposes_enrich_flag_and_it_defaults_off(self):
        proc = subprocess.run(
            [sys.executable, str(REPO / "build_playground_briefings.py"), "--help"],
            capture_output=True, text=True, cwd=str(REPO), timeout=30)
        self.assertEqual(proc.returncode, 0)
        self.assertIn("--enrich", proc.stdout)
        self.assertIn("off by default", proc.stdout)


if __name__ == "__main__":
    unittest.main()
