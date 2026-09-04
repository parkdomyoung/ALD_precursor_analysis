from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.fetch_openalex import fetch_works, reconstruct_abstract, write_outputs


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload
        self.raise_called = False

    def raise_for_status(self):
        self.raise_called = True

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.responses.pop(0)


def work(work_id, title="ALD paper"):
    return {
        "id": work_id,
        "doi": f"https://doi.org/{work_id}",
        "title": title,
        "publication_year": 2024,
        "publication_date": "2024-01-02",
        "abstract_inverted_index": {"atomic": [0], "layer": [1], "deposition": [2]},
    }


class OpenAlexTests(unittest.TestCase):
    def test_reconstruct_abstract_orders_positions(self):
        inverted = {"layer": [1], "atomic": [0], "deposition": [2, 4], "works": [3]}
        self.assertEqual(
            reconstruct_abstract(inverted),
            "atomic layer deposition works deposition",
        )
        self.assertEqual(reconstruct_abstract(None), "")

    def test_cursor_pagination_deduplicates_and_uses_auth_header(self):
        first = FakeResponse(
            {
                "meta": {"count": 3, "next_cursor": "next"},
                "results": [work("W1"), work("W2")],
            }
        )
        second = FakeResponse(
            {
                "meta": {"count": 3, "next_cursor": None},
                "results": [work("W2"), work("W3")],
            }
        )
        session = FakeSession([first, second])

        records, metadata = fetch_works(
            query="ALD",
            start_year=2020,
            end_year=2025,
            max_results=10,
            min_abstract_chars=0,
            api_key="secret-value",
            session=session,
        )

        self.assertEqual([record["openalex_id"] for record in records], ["W1", "W2", "W3"])
        self.assertEqual(metadata["pages_fetched"], 2)
        self.assertEqual(metadata["api_total_candidates"], 3)
        self.assertTrue(first.raise_called and second.raise_called)
        self.assertEqual(
            session.calls[0][1]["headers"]["Authorization"],
            "Bearer secret-value",
        )
        self.assertNotIn("api_key", session.calls[0][1]["params"])
        self.assertEqual(session.calls[0][1]["params"]["per_page"], 10)
        self.assertEqual(session.calls[1][1]["params"]["cursor"], "next")

    def test_invalid_range_is_rejected(self):
        with self.assertRaises(ValueError):
            fetch_works(
                query="ALD",
                start_year=2025,
                end_year=2024,
                max_results=10,
                session=FakeSession([]),
            )

    def test_manifest_never_contains_api_key(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "works.csv"
            _, manifest = write_outputs(
                [
                    {
                        "openalex_id": "W1",
                        "title": "A",
                        "abstract": "B",
                    }
                ],
                {"used_api_key": True, "records_written": 999},
                output,
            )
            manifest_text = manifest.read_text(encoding="utf-8")
            payload = json.loads(manifest_text)
            self.assertEqual(payload["records_written"], 1)
            self.assertNotIn("secret", manifest_text.lower())
            self.assertNotIn("api_key", payload)


if __name__ == "__main__":
    unittest.main()

