from __future__ import annotations

import json
import math
import re
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.schemas import Evidence


TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
PACK_PATTERN = re.compile(r"([a-z]+(?:\\s+[a-z]+)*\\s+\\d+(?:gb|mb)?)", re.IGNORECASE)


class BaseMockConnector(ABC):
    name: str
    source_type: str
    file_name: str

    def __init__(self, sources_dir: Path) -> None:
        self.sources_dir = sources_dir

    @abstractmethod
    def _to_evidence(self, item: dict[str, Any], score: float, matched_terms: list[str]) -> Evidence:
        raise NotImplementedError

    def search(self, query: str, limit: int = 5) -> list[Evidence]:
        query_terms = tokenize(query)
        if not query_terms:
            return []
        results: list[Evidence] = []
        for item in self._load_items():
            text = self._search_text(item)
            matched_terms = sorted(set(query_terms).intersection(tokenize(text)))
            if not matched_terms:
                continue
            score = self._score(query, item, matched_terms)
            results.append(self._to_evidence(item, score, matched_terms))
        return sorted(results, key=lambda evidence: evidence.relevance_score, reverse=True)[:limit]

    def _load_items(self) -> list[dict[str, Any]]:
        path = self.sources_dir / self.file_name
        return json.loads(path.read_text(encoding="utf-8"))

    def _search_text(self, item: dict[str, Any]) -> str:
        title = item.get("title") or item.get("subject") or ""
        return f"{title} {item.get('body', '')}"

    def _score(self, query: str, item: dict[str, Any], matched_terms: list[str]) -> float:
        query_terms = tokenize(query)
        overlap = len(matched_terms) / max(len(set(query_terms)), 1)
        score = overlap
        if _pack_phrase(query) and _pack_phrase(query).lower() in self._search_text(item).lower():
            score += 0.35
        score += freshness_boost(parse_timestamp(item.get("updated_at") or item.get("sent_at")))
        score += priority_boost(item.get("source_priority"))
        score += status_boost(item.get("document_status"))
        return max(0.0, min(1.0, score))


def tokenize(value: str) -> list[str]:
    return TOKEN_PATTERN.findall(value.lower())


def parse_timestamp(value: str | None) -> datetime:
    if not value:
        return datetime(1970, 1, 1, tzinfo=UTC)
    cleaned = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(cleaned)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def make_excerpt(body: str, terms: list[str], max_length: int = 280) -> str:
    if not body:
        return ""
    lowered = body.lower()
    positions = [lowered.find(term.lower()) for term in terms if term.lower() in lowered]
    start = max(min(positions) - 60, 0) if positions else 0
    excerpt = body[start : start + max_length].strip()
    prefix = "..." if start > 0 else ""
    suffix = "..." if start + max_length < len(body) else ""
    return f"{prefix}{excerpt}{suffix}"


def freshness_boost(timestamp: datetime) -> float:
    reference = datetime(2026, 7, 14, tzinfo=UTC)
    age_days = max((reference - timestamp).days, 0)
    return max(0.0, 0.18 * math.exp(-age_days / 60))


def priority_boost(priority: str | None) -> float:
    return {"high": 0.15, "medium": 0.07, "low": 0.0}.get(priority or "", 0.0)


def status_boost(status: str | None) -> float:
    return {"approved": 0.2, "draft": -0.04, "deprecated": -0.12}.get(status or "", 0.0)


def _pack_phrase(query: str) -> str:
    match = PACK_PATTERN.search(query)
    return match.group(1) if match else ""
