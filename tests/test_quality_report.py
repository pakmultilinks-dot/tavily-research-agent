"""Unit tests for the briefing quality report (quality_report.py).

Run from the repo root:
    python3 -m unittest discover -s tests -v

All tests are offline. No Tavily key and no network are needed.
The live JSON and the committed briefing Markdown files are the
only inputs; the numbers asserted here are the measured values
from those files, cross-checked against the README table.
"""
import json
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from quality_report import (
    COMPANIES,
    JSON_PATH,
    MEETING,
    format_company,
    format_report,
    is_profile_url,
    measure_all,
    measure_company,
    parse_md_header,
    share,
)

PROJECT_DIR = Path(__file__).resolve().parents[1]


def load_live_json():
    return json.loads(JSON_PATH.read_text(encoding="utf-8"))


def load_fixture_items():
    data = json.loads(
        (PROJECT_DIR / "examples" / "fixtures.json").read_text(encoding="utf-8"))
    return data["results"]


class TestShare(unittest.TestCase):
    def test_full_share(self):
        self.assertEqual(share(14, 14), "14/14 (100%)")

    def test_partial_share_rounds_to_whole_percent(self):
        self.assertEqual(share(10, 14), "10/14 (71%)")
        self.assertEqual(share(4, 15), "4/15 (27%)")
        self.assertEqual(share(18, 37), "18/37 (49%)")

    def test_empty_denominator_is_not_a_percent(self):
        self.assertEqual(share(0, 0), "0/0 (n/a)")


class TestIsProfileUrl(unittest.TestCase):
    def test_profile_url_is_detected(self):
        self.assertTrue(is_profile_url(
            "https://tavily.com/knowledge/company/p4PyTakV77G9"))

    def test_normal_url_is_not_a_profile(self):
        self.assertFalse(is_profile_url("https://techcrunch.com/2026/10/31/x"))
        self.assertFalse(is_profile_url(""))


class TestParseMdHeader(unittest.TestCase):
    def test_committed_openai_header(self):
        text = (PROJECT_DIR / "examples" / "live-openai" / "briefing.md"
                ).read_text(encoding="utf-8")
        header = parse_md_header(text)
        self.assertEqual(header["kept"], 14)
        self.assertEqual(header["dropped_old"], 0)
        self.assertEqual(header["dropped_duplicates"], 2)
        self.assertEqual(header["dropped_truncated_url"], 1)
        self.assertEqual(header["dropped_profile"], 3)

    def test_committed_microsoft_header(self):
        text = (PROJECT_DIR / "examples" / "live-microsoft" / "briefing.md"
                ).read_text(encoding="utf-8")
        header = parse_md_header(text)
        self.assertEqual(header["kept"], 8)
        self.assertEqual(header["dropped_truncated_url"], 10)
        self.assertEqual(header["dropped_profile"], 2)

    def test_missing_counts_are_none(self):
        header = parse_md_header("no counts here at all")
        self.assertEqual(header, {
            "kept": None,
            "dropped_old": None,
            "dropped_duplicates": None,
            "dropped_truncated_url": None,
            "dropped_profile": None,
        })


class TestMeasureLiveJson(unittest.TestCase):
    def test_openai_measured_values(self):
        data = load_live_json()
        items = [r for r in data["results"] if r["company"] == "OpenAI"]
        m = measure_company("OpenAI", items, MEETING, MEETING)
        self.assertEqual(m["total"], 20)
        self.assertEqual(m["kept"], 14)
        self.assertEqual(m["dropped_truncated_url"], 1)
        self.assertEqual(m["dropped_profile"], 3)
        self.assertEqual(m["dropped_duplicates"], 2)
        self.assertEqual(m["dropped_old"], 0)
        self.assertEqual(m["dated"], (14, 14))
        self.assertEqual(m["with_url"], (14, 14))
        self.assertEqual(m["named_subject"], (10, 14))
        self.assertEqual(m["with_full_content"], (0, 14))
        self.assertEqual(m["date_range"], (date(2026, 10, 8), date(2026, 11, 4)))
        self.assertEqual(m["categories"], ["funding", "hires", "launches", "news"])

    def test_google_and_microsoft_measured_values(self):
        data = load_live_json()
        items = [r for r in data["results"] if r["company"] == "Google"]
        google = measure_company("Google", items, MEETING, MEETING)
        self.assertEqual(google["kept"], 15)
        self.assertEqual(google["dropped_truncated_url"], 5)
        self.assertEqual(google["dropped_profile"], 0)
        self.assertEqual(google["named_subject"], (4, 15))
        items = [r for r in data["results"] if r["company"] == "Microsoft"]
        microsoft = measure_company("Microsoft", items, MEETING, MEETING)
        self.assertEqual(microsoft["kept"], 8)
        self.assertEqual(microsoft["dropped_truncated_url"], 10)
        self.assertEqual(microsoft["dropped_profile"], 2)
        self.assertEqual(microsoft["named_subject"], (4, 8))
        self.assertEqual(microsoft["date_range"],
                         (date(2026, 10, 20), date(2026, 11, 4)))

    def test_totals_are_sums_not_rounded_percents(self):
        measured = measure_all(load_live_json(), MEETING)
        total = measured["total"]
        self.assertEqual(total["total"], 60)
        self.assertEqual(total["kept"], 37)
        self.assertEqual(total["dropped_truncated_url"], 16)
        self.assertEqual(total["dropped_profile"], 5)
        self.assertEqual(total["dropped_duplicates"], 2)
        self.assertEqual(total["dropped_old"], 0)
        self.assertEqual(total["dated"], (37, 37))
        self.assertEqual(total["with_url"], (37, 37))
        self.assertEqual(total["named_subject"], (18, 37))
        self.assertEqual(total["with_full_content"], (0, 37))

    def test_measured_counts_match_committed_markdown_headers(self):
        measured = measure_all(load_live_json(), MEETING)
        for company in COMPANIES:
            slug = {"OpenAI": "openai", "Google": "google",
                    "Microsoft": "microsoft"}[company]
            text = (PROJECT_DIR / "examples" / f"live-{slug}" / "briefing.md"
                    ).read_text(encoding="utf-8")
            header = parse_md_header(text)
            m = measured["per_company"][company]
            self.assertEqual(header["kept"], m["kept"], company)
            self.assertEqual(header["dropped_old"], m["dropped_old"], company)
            self.assertEqual(header["dropped_duplicates"],
                             m["dropped_duplicates"], company)
            self.assertEqual(header["dropped_truncated_url"],
                             m["dropped_truncated_url"], company)
            self.assertEqual(header["dropped_profile"],
                             m["dropped_profile"], company)


class TestMeasureFixtures(unittest.TestCase):
    def test_fixture_sample_measured_values(self):
        items = load_fixture_items()
        m = measure_company("Example Company", items,
                            date(2026, 11, 10), date(2026, 11, 10))
        self.assertEqual(m["total"], 6)
        self.assertEqual(m["kept"], 4)
        self.assertEqual(m["dropped_old"], 1)
        self.assertEqual(m["dropped_duplicates"], 1)
        self.assertEqual(m["dated"], (3, 4))
        self.assertEqual(m["with_url"], (4, 4))
        self.assertEqual(m["named_subject"], (3, 4))
        self.assertEqual(m["with_full_content"], (0, 4))
        self.assertEqual(m["date_range"],
                         (date(2026, 10, 20), date(2026, 11, 2)))

    def test_empty_input_measures_zero(self):
        m = measure_company("Nobody", [], MEETING, MEETING)
        self.assertEqual(m["total"], 0)
        self.assertEqual(m["kept"], 0)
        self.assertEqual(m["dated"], (0, 0))
        self.assertEqual(m["date_range"], (None, None))
        self.assertEqual(m["categories"], [])


class TestFormatReport(unittest.TestCase):
    def test_report_contains_measured_numbers(self):
        measured = measure_all(load_live_json(), MEETING)
        md_check = {c: "yes" for c in COMPANIES}
        report = format_report(measured, md_check)
        self.assertIn("Reproduce: python3 quality_report.py", report)
        self.assertIn("OpenAI: total 20, kept 14", report)
        self.assertIn("Google: total 20, kept 15", report)
        self.assertIn("Microsoft: total 20, kept 8", report)
        self.assertIn("Total: total 60, kept 37", report)
        self.assertIn("title and snippet both name the subject: 18/37 (49%)", report)
        self.assertIn("with full content (Tavily Extract): 0/37 (0%)", report)
        self.assertIn("match the rebuild: yes", report)

    def test_format_company_shows_date_range_and_categories(self):
        measured = measure_all(load_live_json(), MEETING)
        text = format_company(measured["per_company"]["Microsoft"])
        self.assertIn("date range covered: 2026-10-20 to 2026-11-04", text)
        self.assertIn("categories covered:", text)
        self.assertIn("(4 of 4)", text)


if __name__ == "__main__":
    unittest.main()
