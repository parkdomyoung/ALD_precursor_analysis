"""Fetch ALD literature metadata from OpenAlex with reproducible metadata.

The optional ``OPENALEX_API_KEY`` environment variable is sent only in the
Authorization header. It is never written to the CSV, manifest, or logs.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

OPENALEX_WORKS_URL = "https://api.openalex.org/works"
DEFAULT_QUERY = "Atomic Layer Deposition Precursor"
DEFAULT_OUTPUT = Path("artifacts/openalex/ald_openalex_data.csv")
CSV_COLUMNS = (
    "openalex_id",
    "doi",
    "publication_year",
    "publication_date",
    "title",
    "abstract",
)


def reconstruct_abstract(inverted_index: dict[str, list[int]] | None) -> str:
    """Convert an OpenAlex abstract inverted index to plain text."""
    if not inverted_index:
        return ""
    positioned_words = (
        (position, word)
        for word, positions in inverted_index.items()
        for position in positions
    )
    return " ".join(word for _, word in sorted(positioned_words))


def build_session() -> requests.Session:
    """Create a session that retries throttling and transient server errors."""
    retry = Retry(
        total=4,
        connect=4,
        read=4,
        status=4,
        backoff_factor=1.0,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
        respect_retry_after_header=True,
    )
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


def fetch_works(
    *,
    query: str,
    start_year: int,
    end_year: int,
    max_results: int,
    min_abstract_chars: int = 50,
    api_key: str | None = None,
    session: requests.Session | Any | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Fetch and de-duplicate OpenAlex works using cursor pagination."""
    if start_year > end_year:
        raise ValueError("start_year must be less than or equal to end_year")
    if max_results < 1:
        raise ValueError("max_results must be positive")
    if min_abstract_chars < 0:
        raise ValueError("min_abstract_chars must be non-negative")

    client = session or build_session()
    cursor: str | None = "*"
    records: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    pages_fetched = 0
    total_candidates: int | None = None

    headers = {
        "Accept": "application/json",
        "User-Agent": "ALD-precursor-analysis/1.0",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    while cursor and len(records) < max_results:
        params = {
            "search": query,
            "filter": (
                f"from_publication_date:{start_year}-01-01,"
                f"to_publication_date:{end_year}-12-31"
            ),
            "per_page": min(100, max_results - len(records)),
            "cursor": cursor,
            "select": (
                "id,doi,title,publication_year,publication_date,"
                "abstract_inverted_index"
            ),
        }
        response = client.get(
            OPENALEX_WORKS_URL,
            params=params,
            headers=headers,
            timeout=(10, 60),
        )
        response.raise_for_status()
        payload = response.json()
        pages_fetched += 1

        meta = payload.get("meta") or {}
        if total_candidates is None and isinstance(meta.get("count"), int):
            total_candidates = meta["count"]

        results = payload.get("results") or []
        if not results:
            break

        for item in results:
            work_id = item.get("id")
            if not work_id or work_id in seen_ids:
                continue
            seen_ids.add(work_id)

            abstract = reconstruct_abstract(item.get("abstract_inverted_index"))
            if len(abstract) < min_abstract_chars:
                continue

            records.append(
                {
                    "openalex_id": work_id,
                    "doi": item.get("doi") or "",
                    "publication_year": item.get("publication_year"),
                    "publication_date": item.get("publication_date") or "",
                    "title": item.get("title") or "",
                    "abstract": abstract,
                }
            )
            if len(records) >= max_results:
                break

        next_cursor = meta.get("next_cursor")
        cursor = next_cursor if isinstance(next_cursor, str) and next_cursor else None

    metadata = {
        "endpoint": OPENALEX_WORKS_URL,
        "query": query,
        "start_year": start_year,
        "end_year": end_year,
        "requested_max_results": max_results,
        "min_abstract_chars": min_abstract_chars,
        "records_written": len(records),
        "pages_fetched": pages_fetched,
        "api_total_candidates": total_candidates,
        "used_api_key": bool(api_key),
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    return records, metadata


def write_outputs(
    records: Iterable[dict[str, Any]],
    metadata: dict[str, Any],
    output_path: Path,
) -> tuple[Path, Path]:
    """Write the CSV and its JSON provenance manifest."""
    import csv

    materialized = list(records)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path = output_path.with_suffix(output_path.suffix + ".manifest.json")

    with output_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(materialized)

    safe_metadata = dict(metadata)
    safe_metadata["records_written"] = len(materialized)
    with manifest_path.open("w", encoding="utf-8") as handle:
        json.dump(safe_metadata, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")

    return output_path, manifest_path


def parse_args() -> argparse.Namespace:
    current_year = datetime.now(timezone.utc).year
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", default=DEFAULT_QUERY)
    parser.add_argument("--start-year", type=int, default=2015)
    parser.add_argument("--end-year", type=int, default=current_year)
    parser.add_argument("--max-results", type=int, default=2000)
    parser.add_argument("--min-abstract-chars", type=int, default=50)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    api_key = os.getenv("OPENALEX_API_KEY")
    records, metadata = fetch_works(
        query=args.query,
        start_year=args.start_year,
        end_year=args.end_year,
        max_results=args.max_results,
        min_abstract_chars=args.min_abstract_chars,
        api_key=api_key,
    )
    csv_path, manifest_path = write_outputs(records, metadata, args.output)
    print(f"Wrote {len(records)} records to {csv_path}")
    print(f"Wrote provenance manifest to {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

