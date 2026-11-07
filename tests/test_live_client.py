"""Unit tests for the direct Tavily API client key hygiene.

Run from the repo root:
    python3 -m unittest discover -s tests -v

All tests are offline. The HTTP layer is mocked with
unittest.mock, so no Tavily key and no network are needed.
No test here makes a live call, and no key value is written
to any file. The fake keys below are invented test strings.
"""
import os
import unittest
from unittest.mock import patch

import requests

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tavily_agent.tavily_client import (
    TavilyAuthError,
    get_api_key,
    key_format_warning,
    search_category,
    smoke_check,
)

FAKE_KEY = "tvly-testkey-123"


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {"results": []}

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


def ok_payload():
    return {"results": [
        {"title": "OpenAI news", "url": "https://example.com/openai-news",
         "content": "OpenAI did something new.",
         "score": 0.9, "published_date": "Tue, 03 Nov 2026 08:00:00 GMT"},
    ]}


def post_200(*args, **kwargs):
    return FakeResponse(200, ok_payload())


class TestKeyHygiene(unittest.TestCase):
    def test_empty_key_rejected_before_any_network_call(self):
        with patch.dict(os.environ, {"TAVILY_API_KEY": "   "}):
            with patch("tavily_agent.tavily_client.requests.post") as mock_post:
                with self.assertRaises(RuntimeError):
                    search_category("OpenAI", "news", "2026-10-06", "2026-11-05")
                mock_post.assert_not_called()

    def test_key_with_surrounding_spaces_is_trimmed(self):
        with patch.dict(os.environ, {"TAVILY_API_KEY": f"  {FAKE_KEY}  "}):
            with patch("tavily_agent.tavily_client.requests.post",
                       return_value=FakeResponse(200, ok_payload())) as mock_post:
                search_category("OpenAI", "news", "2026-10-06", "2026-11-05")
                headers = mock_post.call_args.kwargs["headers"]
                self.assertEqual(headers["Authorization"], f"Bearer {FAKE_KEY}")

    def test_get_api_key_returns_the_trimmed_key(self):
        with patch.dict(os.environ, {"TAVILY_API_KEY": f"  {FAKE_KEY}  "}):
            self.assertEqual(get_api_key(), FAKE_KEY)

    def test_key_format_warning_only_warns_never_rejects(self):
        warning = key_format_warning("abc123-not-a-tavily-key")
        self.assertIsNotNone(warning)
        self.assertIn("tvly-", warning)
        self.assertIsNone(key_format_warning("tvly-abcdef"))
        self.assertIsNone(key_format_warning(""))
        # A key with the wrong format is still sent, not rejected.
        with patch.dict(os.environ, {"TAVILY_API_KEY": "abc123"}):
            with patch("tavily_agent.tavily_client.requests.post",
                       return_value=FakeResponse(200, ok_payload())) as mock_post:
                results = search_category("OpenAI", "news", "2026-10-06", "2026-11-05")
                self.assertEqual(len(results), 1)
                mock_post.assert_called_once()


class TestMockedSearch(unittest.TestCase):
    def test_mocked_200_returns_parsed_results(self):
        with patch.dict(os.environ, {"TAVILY_API_KEY": FAKE_KEY}):
            with patch("tavily_agent.tavily_client.requests.post",
                       side_effect=post_200):
                results = search_category("OpenAI", "news", "2026-10-06", "2026-11-05")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "OpenAI news")
        self.assertEqual(results[0]["url"], "https://example.com/openai-news")
        self.assertEqual(results[0]["published"].isoformat(), "2026-11-03")

    def test_mocked_401_raises_clear_error_and_is_not_retried(self):
        with patch.dict(os.environ, {"TAVILY_API_KEY": FAKE_KEY}):
            with patch("tavily_agent.tavily_client.requests.post",
                       return_value=FakeResponse(401, {})) as mock_post:
                with self.assertRaises(TavilyAuthError) as ctx:
                    search_category("OpenAI", "news", "2026-10-06", "2026-11-05")
        self.assertIn("app.tavily.com", str(ctx.exception))
        self.assertIn("TAVILY_API_KEY", str(ctx.exception))
        self.assertIn("401", str(ctx.exception))
        # Never retried on 401: exactly one call.
        self.assertEqual(mock_post.call_count, 1)
        # The key value itself is never in the error.
        self.assertNotIn(FAKE_KEY, str(ctx.exception))

    def test_mocked_timeout_retries_once_then_succeeds(self):
        with patch.dict(os.environ, {"TAVILY_API_KEY": FAKE_KEY}):
            with patch("tavily_agent.tavily_client.requests.post",
                       side_effect=[requests.Timeout("slow"),
                                    FakeResponse(200, ok_payload())]) as mock_post:
                results = search_category("OpenAI", "news", "2026-10-06", "2026-11-05")
        self.assertEqual(len(results), 1)
        self.assertEqual(mock_post.call_count, 2)

    def test_mocked_timeout_twice_raises_after_one_retry(self):
        with patch.dict(os.environ, {"TAVILY_API_KEY": FAKE_KEY}):
            with patch("tavily_agent.tavily_client.requests.post",
                       side_effect=requests.Timeout("slow")) as mock_post:
                with self.assertRaises(RuntimeError) as ctx:
                    search_category("OpenAI", "news", "2026-10-06", "2026-11-05")
        self.assertIn("timed out", str(ctx.exception))
        self.assertEqual(mock_post.call_count, 2)
        self.assertNotIn(FAKE_KEY, str(ctx.exception))


class TestSmokeCheck(unittest.TestCase):
    def test_smoke_check_mocked_ok_reports_results_only(self):
        with patch.dict(os.environ, {"TAVILY_API_KEY": FAKE_KEY}):
            with patch("tavily_agent.tavily_client.requests.post",
                       side_effect=post_200):
                result = smoke_check()
        self.assertEqual(result, {"ok": True, "results": 1})

    def test_smoke_check_mocked_401_raises_auth_error(self):
        with patch.dict(os.environ, {"TAVILY_API_KEY": FAKE_KEY}):
            with patch("tavily_agent.tavily_client.requests.post",
                       return_value=FakeResponse(401, {})):
                with self.assertRaises(TavilyAuthError):
                    smoke_check()


if __name__ == "__main__":
    unittest.main()
