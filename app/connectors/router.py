from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from app.config import Settings, get_settings
from app.connectors.base import make_excerpt, parse_timestamp
from app.connectors.mock_confluence import MockConfluenceConnector
from app.connectors.mock_inbox import MockInboxConnector
from app.connectors.mock_wiki import MockWikiConnector
from app.schemas import Evidence


PACK_NAME_PATTERN = re.compile(r"\b[A-Z][A-Za-z]+(?:\s+[A-Z]?[A-Za-z]+)*\s+\d+(?:GB|MB)?\b")


def get_connectors(settings: Settings | None = None):
    settings = settings or get_settings()
    return [
        MockConfluenceConnector(settings.mock_sources_dir),
        MockWikiConnector(settings.mock_sources_dir),
        MockInboxConnector(settings.mock_sources_dir),
    ]


def search_all_sources(
    query: str,
    limit_per_source: int = 5,
    top_k: int = 10,
    settings: Settings | None = None,
) -> list[Evidence]:
    seen: dict[str, Evidence] = {}
    for connector in get_connectors(settings):
        for evidence in connector.search(query, limit=limit_per_source):
            existing = seen.get(evidence.source_id)
            if existing is None or evidence.relevance_score > existing.relevance_score:
                seen[evidence.source_id] = evidence
    return sorted(
        seen.values(),
        key=lambda item: (item.relevance_score, item.timestamp),
        reverse=True,
    )[:top_k]


def source_stats(settings: Settings | None = None) -> dict[str, Any]:
    settings = settings or get_settings()
    metadata_path = settings.mock_sources_dir / "source_metadata.json"
    metadata = _read_json(metadata_path, {})
    return {
        "mock_sources_dir": str(settings.mock_sources_dir),
        "real_connectors_used": False,
        "source_counts": metadata.get("source_counts", {}),
        "connectors": [
            {"name": connector.name, "source_type": connector.source_type}
            for connector in get_connectors(settings)
        ],
    }


def load_source_documents(settings: Settings | None = None) -> list[dict[str, Any]]:
    settings = settings or get_settings()
    documents = (
        [_normalize_confluence(item) for item in _read_json(settings.mock_sources_dir / "confluence_pages.json", [])]
        + [_normalize_wiki(item) for item in _read_json(settings.mock_sources_dir / "wiki_pages.json", [])]
        + [_normalize_email(item) for item in _read_json(settings.mock_sources_dir / "inbox_emails.json", [])]
    )
    return sorted(documents, key=lambda item: item["timestamp"], reverse=True)


def get_source_document(source_id: str, settings: Settings | None = None) -> dict[str, Any] | None:
    for document in load_source_documents(settings):
        if document["source_id"] == source_id:
            return document
    return None


def _normalize_confluence(item: dict[str, Any]) -> dict[str, Any]:
    body = item.get("body", "")
    timestamp = parse_timestamp(item.get("updated_at")).isoformat()
    return {
        **item,
        "source_id": item["source_id"],
        "source_type": "confluence",
        "title_or_subject": item["title"],
        "author_or_owner": item.get("owner_team"),
        "timestamp": timestamp,
        "source_priority": item.get("source_priority", "medium"),
        "document_status": item.get("document_status", "n/a"),
        "tags": [],
        "labels": [],
        "body": body,
        "excerpt": make_excerpt(body, []),
        "matched_terms": [],
        "related_pack_names": related_pack_names(body),
    }


def _normalize_wiki(item: dict[str, Any]) -> dict[str, Any]:
    body = item.get("body", "")
    timestamp = parse_timestamp(item.get("updated_at")).isoformat()
    return {
        **item,
        "source_id": item["source_id"],
        "source_type": "wiki",
        "title_or_subject": item["title"],
        "author_or_owner": item.get("owner_team"),
        "timestamp": timestamp,
        "source_priority": "medium",
        "document_status": "n/a",
        "labels": [],
        "body": body,
        "excerpt": make_excerpt(body, []),
        "matched_terms": [],
        "related_pack_names": related_pack_names(body),
    }


def _normalize_email(item: dict[str, Any]) -> dict[str, Any]:
    body = item.get("body", "")
    timestamp = parse_timestamp(item.get("sent_at")).isoformat()
    labels = item.get("labels", [])
    return {
        **item,
        "source_id": item["source_id"],
        "source_type": "email",
        "title_or_subject": item["subject"],
        "author_or_owner": item.get("from"),
        "timestamp": timestamp,
        "source_priority": "medium",
        "document_status": "approved" if "approved" in labels else "n/a",
        "tags": [],
        "body": body,
        "excerpt": make_excerpt(body, []),
        "matched_terms": [],
        "related_pack_names": related_pack_names(body),
    }


def related_pack_names(text: str) -> list[str]:
    names = {match.group(0).strip() for match in PACK_NAME_PATTERN.finditer(text)}
    return sorted(names)


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))
