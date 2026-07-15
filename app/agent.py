from __future__ import annotations

from app.config import Settings
from app.connectors.router import search_all_sources
from app.llm import GeminiProvider, fallback_update
from app.schemas import AnalysisMode, MissingFieldIssue, ProcessingMode, ProposedUpdate, TariffRecord


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
) -> tuple[list[ProposedUpdate], ProcessingMode]:
    provider = GeminiProvider(settings) if generation_mode == "gemini" else None
    records_by_id = {record.pack_id: record for record in records}
    proposals: list[ProposedUpdate] = []
    modes: list[ProcessingMode] = []

    for issue in issues:
        record = records_by_id.get(issue.pack_id)
        if not record:
            continue
        evidence = search_all_sources(build_issue_query(record, issue), settings=settings, top_k=6)
        if provider is None:
            proposal = fallback_update(record, issue, evidence)
            mode = "preview"
        else:
            proposal, mode = provider.propose_update(record, issue, evidence)
        proposals.append(proposal)
        modes.append(mode)

    return deduplicate_proposals(proposals), _summarize_mode(modes)


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
