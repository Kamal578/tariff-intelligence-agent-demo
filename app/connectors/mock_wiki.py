from __future__ import annotations

from typing import Any

from app.connectors.base import BaseMockConnector, make_excerpt, parse_timestamp
from app.schemas import Evidence


class MockWikiConnector(BaseMockConnector):
    name = "Mock Wiki"
    source_type = "wiki"
    file_name = "wiki_pages.json"

    def _to_evidence(self, item: dict[str, Any], score: float, matched_terms: list[str]) -> Evidence:
        return Evidence(
            source_id=item["source_id"],
            source_type="wiki",
            title_or_subject=item["title"],
            author_or_owner=item.get("owner_team"),
            timestamp=parse_timestamp(item["updated_at"]),
            fake_url=item["fake_url"],
            excerpt=make_excerpt(item.get("body", ""), matched_terms),
            relevance_score=score,
            source_priority="medium",
            document_status="n/a",
            matched_terms=matched_terms,
        )
