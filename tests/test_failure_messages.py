"""Unit tests for the shown failure handling in the Streamlit app.

Run from the repo root:
    python3 -m unittest discover -s tests -v

All tests are offline. No Tavily key and no network are needed.
The three failure cases are the honest ones from the code:
no key set, wrong key (HTTP 401), and no results found. Each
message asserted here is the exact message the app shows, taken
from the code that produces it, not invented for the test.
"""
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tavily_agent.briefing import build_briefing
from tavily_agent.tavily_client import AUTH_FIX_MESSAGE

PROJECT_DIR = Path(__file__).resolve().parents[1]
APP_PATH = PROJECT_DIR / "app.py"
CLIENT_PATH = PROJECT_DIR / "tavily_agent" / "tavily_client.py"

# The exact on-screen messages, copied from the code that shows them.
NO_KEY_MESSAGE = "Live mode needs a Tavily key. Enter your own key above."
NO_RESULTS_MESSAGE = (
    "No verified developments in this window. Nothing is listed here on purpose."
)


def app_source() -> str:
    return APP_PATH.read_text(encoding="utf-8")


class TestFailureMessagesShownInApp(unittest.TestCase):
    def test_no_key_message_is_in_the_app(self):
        source = app_source()
        self.assertIn(NO_KEY_MESSAGE, source)
        self.assertIn("What if it fails", source)

    def test_401_message_is_defined_in_client_and_shown_in_app(self):
        client = CLIENT_PATH.read_text(encoding="utf-8")
        self.assertIn(
            "Tavily rejected the key with HTTP 401 Unauthorized.", client)
        source = app_source()
        self.assertIn("AUTH_FIX_MESSAGE", source)
        self.assertIn("Search failed: ", source)

    def test_no_results_message_is_in_the_app(self):
        self.assertIn(NO_RESULTS_MESSAGE, app_source())

    def test_failure_section_lists_all_three_cases(self):
        # The section renders the three messages through the
        # constants, so it references each constant by name. The
        # constants themselves hold the exact messages asserted
        # in the tests above, so what the section shows is those
        # exact messages.
        source = app_source()
        section = source[source.index("What if it fails"):]
        self.assertIn("NO_KEY_MESSAGE", section)
        self.assertIn("AUTH_FIX_MESSAGE", section)
        self.assertIn("NO_RESULTS_MESSAGE", section)
        self.assertIn("- No key:", section)
        self.assertIn("- Wrong key: Search failed: ", section)
        self.assertIn("- No results:", section)


class TestFailureMessagesAtRuntime(unittest.TestCase):
    def test_401_message_names_the_fix(self):
        self.assertTrue(AUTH_FIX_MESSAGE.startswith(
            "Tavily rejected the key with HTTP 401 Unauthorized."))
        self.assertIn("https://app.tavily.com/home", AUTH_FIX_MESSAGE)
        self.assertIn("TAVILY_API_KEY", AUTH_FIX_MESSAGE)
        self.assertIn("Never paste a real key", AUTH_FIX_MESSAGE)

    def test_empty_briefing_summary_is_the_no_results_message(self):
        briefing = build_briefing("Nobody", date(2026, 11, 5), [],
                                  mode="live", today=date(2026, 11, 5))
        self.assertIn("No results were found for 'Nobody'", briefing.summary)
        self.assertIn("No developments are listed, because none were verified.",
                      briefing.summary)
        self.assertEqual(briefing.results, [])


if __name__ == "__main__":
    unittest.main()
