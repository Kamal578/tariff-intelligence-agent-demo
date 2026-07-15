from __future__ import annotations

from app.config import Settings
from app.connectors.router import search_all_sources
from app.llm import GeminiProvider
from app.schemas import MissingFieldIssue, ProposedUpdate, TariffRecord


def build_issue_query(record: TariffRecord, issue: MissingFieldIssue) -> str:
    return (
        f"{record.pack_name} {record.tariff_name or ''} {issue.field_name} "
        f"{issue.issue_type} latest approved value tariff pack policy rename discontinued activation price"
    )


def generate_proposals(
    records: list[TariffRecord],
    issues: list[MissingFieldIssue],
    settings: Settings,
) -> tuple[list[ProposedUpdate], str]:
    provider = GeminiProvider(settings)
    records_by_id = {record.pack_id: record for record in records}
    proposals: list[ProposedUpdate] = []
    modes: list[str] = []

    for issue in issues:
        record = records_by_id.get(issue.pack_id)
        if not record:
            continue
        evidence = search_all_sources(build_issue_query(record, issue), settings=settings, top_k=6)
        proposal, mode = provider.propose_update(record, issue, evidence)
        proposals.append(proposal)
        modes.append(mode)

    return deduplicate_proposals(proposals), _summarize_mode(modes)


def deduplicate_proposals(proposals: list[ProposedUpdate]) -> list[ProposedUpdate]:
    best: dict[tuple[str, str], ProposedUpdate] = {}
    for proposal in proposals:
        key = (proposal.pack_id, proposal.field_name)
        existing = best.get(key)
        if existing is None or proposal.confidence_score > existing.confidence_score:
            best[key] = proposal
    return sorted(best.values(), key=lambda item: (item.pack_id, item.field_name))


def _summarize_mode(modes: list[str]) -> str:
    unique_modes = set(modes)
    if unique_modes == {"gemini"}:
        return "gemini"
    if unique_modes == {"fallback"} or not unique_modes:
        return "fallback"
    return "mixed"
