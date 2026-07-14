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
        if not (item.pack_id == decision.pack_id and item.field_name == decision.field_name)
    ]
    decisions.append(decision)
    write_json(settings.review_state_path, [item.model_dump(mode="json") for item in decisions])

    proposals = load_proposals_state(settings)
    updated: list[ProposedUpdate] = []
    for proposal in proposals:
        if proposal.pack_id == decision.pack_id and proposal.field_name == decision.field_name:
            proposal.status = decision.decision
        updated.append(proposal)
    write_json(settings.proposals_state_path, [item.model_dump(mode="json") for item in updated])
    return updated
