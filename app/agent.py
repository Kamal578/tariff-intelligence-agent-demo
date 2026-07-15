from __future__ import annotations

import time
from typing import Callable

from app.config import Settings
from app.connectors.router import search_all_sources
from app.llm import GeminiProvider, fallback_update
from app.schemas import AnalysisMode, MissingFieldIssue, ProcessingMode, ProposedUpdate, TariffRecord

ProgressCallback = Callable[[str, int], None]


def build_issue_query(record: TariffRecord, issue: MissingFieldIssue) -> str:
    return (
        f"{record.pack_name} {record.tariff_name or ''} {issue.field_name} "
        f"{issue.issue_type} latest approved value tariff pack policy rename discontinued activation price"
    )


def generate_proposals(
    records: list[TariffRecord],
    issues: list[MissingFieldIssue],
    settings: Settings,
    generation_mode: AnalysisMode = "preview",
    progress_callback: ProgressCallback | None = None,
) -> tuple[list[ProposedUpdate], ProcessingMode]:
    provider = GeminiProvider(settings) if generation_mode == "gemini" else None
    records_by_id = {record.pack_id: record for record in records}
    proposals: list[ProposedUpdate] = []
    modes: list[ProcessingMode] = []
    total_issues = max(len(issues), 1)

    for index, issue in enumerate(issues, start=1):
        record = records_by_id.get(issue.pack_id)
        if not record:
            continue
        progress = 50 + int((index - 1) / total_issues * 34)
        _emit(
            progress_callback,
            f"Retrieving evidence {index}/{len(issues)}: {issue.pack_name} {issue.field_name}",
            progress,
        )
        _pause_for_visible_progress(settings, progress_callback)
        evidence = search_all_sources(build_issue_query(record, issue), settings=settings, top_k=6)
        _emit(
            progress_callback,
            f"Generating proposal {index}/{len(issues)}: {issue.issue_type}",
            min(84, progress + 1),
        )
        _pause_for_visible_progress(settings, progress_callback)
        if provider is None:
            proposal = fallback_update(record, issue, evidence)
            mode = "preview"
        else:
            proposal, mode = provider.propose_update(record, issue, evidence)
        proposals.append(proposal)
        modes.append(mode)

    _emit(progress_callback, "Deduplicating and ranking proposals", 84)
    return deduplicate_proposals(proposals), _summarize_mode(modes)


def _emit(callback: ProgressCallback | None, stage: str, progress: int) -> None:
    if callback:
        callback(stage, progress)


def _pause_for_visible_progress(settings: Settings, callback: ProgressCallback | None) -> None:
    if callback and settings.analysis_progress_delay_ms > 0:
        time.sleep(settings.analysis_progress_delay_ms / 1000)


def deduplicate_proposals(proposals: list[ProposedUpdate]) -> list[ProposedUpdate]:
    best: dict[tuple[str, str], ProposedUpdate] = {}
    for proposal in proposals:
        key = (proposal.pack_id, proposal.field_name)
        existing = best.get(key)
        if existing is None or _proposal_rank(proposal) > _proposal_rank(existing):
            best[key] = proposal
    return sorted(best.values(), key=lambda item: (item.pack_id, item.field_name))


def _proposal_rank(proposal: ProposedUpdate) -> tuple[int, float]:
    risk_rank = {"low": 1, "medium": 2, "high": 3}[proposal.risk_level]
    return risk_rank, proposal.confidence_score


def _summarize_mode(modes: list[ProcessingMode]) -> ProcessingMode:
    unique_modes = set(modes)
    if unique_modes == {"preview"}:
        return "preview"
    if unique_modes == {"gemini"}:
        return "gemini"
    if unique_modes == {"fallback"} or not unique_modes:
        return "fallback"
    return "mixed"
