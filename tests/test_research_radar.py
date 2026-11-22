"""Offline tests for agent/scripts/research_radar.py (no network)."""
import importlib.util
import unittest
from datetime import UTC, datetime
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "research_radar", Path(__file__).resolve().parents[1] / "agent" / "scripts" / "research_radar.py")
radar = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(radar)

ARXIV_FEED = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2611.01234v2</id>
    <published>2026-11-20T17:00:00Z</published>
    <title>Auditing   Federated
      Learning</title>
    <summary>We audit privacy leakage in federated learning.</summary>
    <author><name>A. Author</name></author>
    <author><name>B. Author</name></author>
  </entry>
  <entry>
    <id>http://arxiv.org/abs/2601.00001v1</id>
    <published>2026-01-02T10:00:00Z</published>
    <title>Old paper</title>
    <summary>Too old.</summary>
    <author><name>C. Author</name></author>
  </entry>
</feed>"""

OPENALEX_PAGE = {
    "results": [{
        "id": "https://openalex.org/W123",
        "doi": "https://doi.org/10.1/abc",
        "title": "A paper that cites you",
        "publication_date": "2026-11-15",
        "authorships": [
            {"author": {"display_name": "D. Researcher"},
             "institutions": [{"display_name": "Some University"}]},
        ],
        "primary_location": {"source": {"display_name": "PoPETs"}},
    }]
}


class ArxivTests(unittest.TestCase):
    def test_parse_filters_by_date_and_normalises(self):
        since = datetime(2026, 11, 1, tzinfo=UTC)
        papers = radar.parse_arxiv(ARXIV_FEED, since)
        self.assertEqual(len(papers), 1)
        p = papers[0]
        self.assertEqual(p["id"], "arxiv:2611.01234")
        self.assertEqual(p["title"], "Auditing Federated Learning")
        self.assertEqual(p["authors"], ["A. Author", "B. Author"])
        self.assertEqual(p["link"], "https://arxiv.org/abs/2611.01234")
        self.assertEqual(p["date"], "2026-11-20")

    def test_query_url_adds_categories(self):
        url = radar.arxiv_query_url('abs:"federated learning"', ["cs.CR", "cs.LG"], 10)
        self.assertIn("export.arxiv.org", url)
        self.assertIn("cat%3Acs.CR+OR+cat%3Acs.LG", url)
        self.assertIn("sortBy=submittedDate", url)


class OpenAlexTests(unittest.TestCase):
    def test_parse_citing(self):
        works = radar.parse_citing(OPENALEX_PAGE)
        self.assertEqual(works[0]["id"], "openalex:W123")
        self.assertEqual(works[0]["institutions"], ["Some University"])
        self.assertEqual(works[0]["venue"], "PoPETs")
        self.assertEqual(works[0]["link"], "https://doi.org/10.1/abc")

    def test_short_id(self):
        self.assertEqual(radar.short_openalex_id("https://openalex.org/A5000000001"), "A5000000001")


class RenderTests(unittest.TestCase):
    def test_empty_run_says_so(self):
        self.assertTrue(radar.render([], [], []).startswith("NO_NEW_PAPERS"))

    def test_sections(self):
        text = radar.render(radar.parse_citing(OPENALEX_PAGE), [], ["note"])
        self.assertIn("=== CITING YOUR WORK", text)
        self.assertIn("=== NOTES", text)


if __name__ == "__main__":
    unittest.main()
