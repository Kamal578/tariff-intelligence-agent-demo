from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from app.agent import generate_proposals
from app.config import Settings, get_settings
from app.excel_io import load_tariff_records
from app.schemas import AnalysisMode, MissingFieldIssue, ProcessingResult, ProposedUpdate, TariffRecord
from app.tools import detect_record_issues
from app.connectors.router import source_stats


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
    return source_stats(settings)


ProgressCallback = Callable[[str, int], None]


def process_tariffs(
    settings: Settings | None = None,
    generation_mode: AnalysisMode = "preview",
    progress_callback: ProgressCallback | None = None,
) -> ProcessingResult:
    settings = settings or get_settings()
    _emit(progress_callback, "Loading Excel workbook", 15)
    records = load_tariff_records(settings.input_excel_path)
    _emit(progress_callback, "Running deterministic validation", 30)
    issues = detect_record_issues(records)
    _emit(progress_callback, "Retrieving source evidence", 50)
    proposals, mode = generate_proposals(records, issues, settings, generation_mode=generation_mode)
    _emit(progress_callback, "Persisting review queue", 86)
    result = ProcessingResult(records=records, issues=issues, proposals=proposals, mode=mode)
    persist_processing_result(result, settings)
    _emit(progress_callback, "Ready for analyst review", 100)
    return result


def _emit(callback: ProgressCallback | None, stage: str, progress: int) -> None:
    if callback:
        callback(stage, progress)


def persist_processing_result(result: ProcessingResult, settings: Settings) -> None:
    write_json(
        settings.records_state_path,
        [record.model_dump(mode="json") for record in result.records],
    )
    write_json(
        settings.proposals_state_path,
        [proposal.model_dump(mode="json") for proposal in result.proposals],
    )
    write_json(
        settings.issues_state_path,
        [issue.model_dump(mode="json") for issue in result.issues],
    )


def load_records_state(settings: Settings | None = None) -> list[TariffRecord]:
    settings = settings or get_settings()
    return [TariffRecord.model_validate(item) for item in read_json(settings.records_state_path, [])]


def load_proposals_state(settings: Settings | None = None) -> list[ProposedUpdate]:
    settings = settings or get_settings()
    return [ProposedUpdate.model_validate(item) for item in read_json(settings.proposals_state_path, [])]


def load_issues_state(settings: Settings | None = None) -> list[MissingFieldIssue]:
    settings = settings or get_settings()
    return [MissingFieldIssue.model_validate(item) for item in read_json(settings.issues_state_path, [])]
