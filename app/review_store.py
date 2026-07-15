from __future__ import annotations

from app.config import Settings, get_settings
from app.pipeline import load_proposals_state, read_json, write_json
from app.schemas import ProposedUpdate, ReviewDecision


def load_review_decisions(settings: Settings | None = None) -> list[ReviewDecision]:
    settings = settings or get_settings()
    return [ReviewDecision.model_validate(item) for item in read_json(settings.review_state_path, [])]


def save_review_decision(
    decision: ReviewDecision,
    settings: Settings | None = None,
) -> list[ProposedUpdate]:
    settings = settings or get_settings()
    decisions = load_review_decisions(settings)
    decisions = [
        item
        for item in decisions
        if not _same_decision_target(item, decision)
    ]
    decisions.append(decision)
    write_json(settings.review_state_path, [item.model_dump(mode="json") for item in decisions])

    proposals = load_proposals_state(settings)
    updated: list[ProposedUpdate] = []
    for proposal in proposals:
        if _proposal_matches_decision(proposal, decision):
            proposal.status = decision.decision
        updated.append(proposal)
    write_json(settings.proposals_state_path, [item.model_dump(mode="json") for item in updated])
    return updated


def _proposal_matches_decision(proposal: ProposedUpdate, decision: ReviewDecision) -> bool:
    if decision.proposal_id:
        return proposal.proposal_id == decision.proposal_id
    return proposal.pack_id == decision.pack_id and proposal.field_name == decision.field_name


def _same_decision_target(left: ReviewDecision, right: ReviewDecision) -> bool:
    if left.proposal_id and right.proposal_id:
        return left.proposal_id == right.proposal_id
    return left.pack_id == right.pack_id and left.field_name == right.field_name
