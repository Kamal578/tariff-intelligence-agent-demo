from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.config import Settings, get_settings
from app.connectors.mock_confluence import MockConfluenceConnector
from app.connectors.mock_inbox import MockInboxConnector
from app.connectors.mock_wiki import MockWikiConnector
from app.schemas import Evidence


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


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))
