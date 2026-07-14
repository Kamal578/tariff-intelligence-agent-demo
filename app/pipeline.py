from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.agent import generate_proposals
from app.config import Settings, get_settings
from app.excel_io import load_tariff_records
from app.schemas import ProcessingResult, ProposedUpdate, TariffRecord
from app.tools import detect_record_issues
from app.vectorstore import build_vectorstore


def write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return path


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def ingest_knowledge(settings: Settings | None = None) -> dict[str, Any]:
    settings = settings or get_settings()
    count = build_vectorstore(settings.knowledge_base_dir, settings.chroma_dir)
    return {"indexed_chunks": count, "chroma_dir": str(settings.chroma_dir)}


def process_tariffs(settings: Settings | None = None) -> ProcessingResult:
    settings = settings or get_settings()
    if not settings.chroma_dir.exists():
        ingest_knowledge(settings)
    records = load_tariff_records(settings.input_excel_path)
    issues = detect_record_issues(records)
    proposals, mode = generate_proposals(records, issues, settings)
    result = ProcessingResult(records=records, issues=issues, proposals=proposals, mode=mode)
    persist_processing_result(result, settings)
    return result


def persist_processing_result(result: ProcessingResult, settings: Settings) -> None:
    write_json(
        settings.records_state_path,
        [record.model_dump(mode="json") for record in result.records],
    )
    write_json(
        settings.proposals_state_path,
        [proposal.model_dump(mode="json") for proposal in result.proposals],
    )


def load_records_state(settings: Settings | None = None) -> list[TariffRecord]:
    settings = settings or get_settings()
    return [TariffRecord.model_validate(item) for item in read_json(settings.records_state_path, [])]


def load_proposals_state(settings: Settings | None = None) -> list[ProposedUpdate]:
    settings = settings or get_settings()
    return [ProposedUpdate.model_validate(item) for item in read_json(settings.proposals_state_path, [])]
