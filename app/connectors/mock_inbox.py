from __future__ import annotations

from typing import Any

from app.connectors.base import BaseMockConnector, make_excerpt, parse_timestamp
from app.schemas import Evidence


class MockInboxConnector(BaseMockConnector):
    name = "Mock Inbox"
    source_type = "email"
    file_name = "inbox_emails.json"

    def _to_evidence(self, item: dict[str, Any], score: float, matched_terms: list[str]) -> Evidence:
        return Evidence(
            source_id=item["source_id"],
            source_type="email",
            title_or_subject=item["subject"],
            author_or_owner=item.get("from"),
            timestamp=parse_timestamp(item["sent_at"]),
            fake_url=item["fake_url"],
            excerpt=make_excerpt(item.get("body", ""), matched_terms),
            relevance_score=score,
            source_priority="medium",
            document_status="approved" if "approved" in item.get("labels", []) else "n/a",
            matched_terms=matched_terms,
        )
