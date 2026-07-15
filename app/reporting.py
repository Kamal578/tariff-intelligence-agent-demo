from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile

from app.config import Settings, get_settings
from app.excel_io import load_tariff_dataframe, write_tariff_dataframe
from app.pipeline import load_proposals_state, read_json, write_json
from app.review_store import load_review_decisions
from app.schemas import ProposedUpdate, ReviewDecision
from app.tools import apply_updates_to_dataframe


def apply_approved_updates(settings: Settings | None = None) -> dict[str, Any]:
    settings = settings or get_settings()
    proposals = load_proposals_state(settings)
    decisions = load_review_decisions(settings)
    approved = _approved_proposals(proposals, decisions)

    source_df = load_tariff_dataframe(settings.input_excel_path)
    updated_df = apply_updates_to_dataframe(source_df, approved)
    output_path = write_tariff_dataframe(updated_df, settings.updated_excel_path)
    audit_log = build_audit_log(proposals, decisions)
    write_json(settings.audit_log_path, audit_log)
    _mark_applied(proposals, approved, settings)
    report_path = generate_markdown_report(proposals, decisions, settings)
    return {
        "applied_updates": len(approved),
        "output_excel": str(output_path),
        "audit_log": str(settings.audit_log_path),
        "report": str(report_path),
        "package": str(build_run_package(settings)),
    }


def build_run_package(settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    if not settings.report_path.exists():
        generate_markdown_report(settings=settings)

    files = [
        (settings.input_excel_path, "input/tariff_packs.xlsx"),
        (settings.records_state_path, "state/records.json"),
        (settings.issues_state_path, "state/issues.json"),
        (settings.proposals_state_path, "state/proposals.json"),
        (settings.review_state_path, "state/review_decisions.json"),
        (settings.audit_log_path, "audit/audit_log.json"),
        (settings.report_path, "audit/review_report.md"),
        (settings.analysis_runs_path, "runs/analysis_runs.json"),
        (settings.updated_excel_path, "output/updated_tariff_packs.xlsx"),
    ]
    settings.run_package_path.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(settings.run_package_path, "w", compression=ZIP_DEFLATED) as archive:
        for path, archive_name in files:
            if path.exists():
                archive.write(path, archive_name)
    return str(settings.run_package_path)


def build_audit_log(
    proposals: list[ProposedUpdate],
    decisions: list[ReviewDecision],
) -> list[dict[str, Any]]:
    proposal_lookup = {(item.pack_id, item.field_name): item for item in proposals}
    proposal_id_lookup = {item.proposal_id: item for item in proposals}
    rows: list[dict[str, Any]] = []
    for decision in decisions:
        proposal = (
            proposal_id_lookup.get(decision.proposal_id)
            if decision.proposal_id
            else proposal_lookup.get((decision.pack_id, decision.field_name))
        )
        rows.append(
            {
                "timestamp": decision.decided_at.isoformat(),
                "proposal_id": proposal.proposal_id if proposal else decision.proposal_id,
                "pack_id": decision.pack_id,
                "pack_name": proposal.pack_name if proposal else None,
                "field_name": decision.field_name,
                "old_value": proposal.old_value if proposal else None,
                "proposed_value": proposal.proposed_value if proposal else None,
                "issue_type": proposal.issue_type if proposal else None,
                "decision": decision.decision,
                "reviewer": decision.reviewer,
                "review_reasoning": decision.reasoning,
                "confidence_score": proposal.confidence_score if proposal else None,
                "risk_level": proposal.risk_level if proposal else None,
                "source_conflict_detected": proposal.source_conflict_detected if proposal else None,
                "evidence_sources": [
                    item.model_dump(mode="json") for item in proposal.evidence_sources
                ]
                if proposal
                else [],
                "agent_reasoning": proposal.reasoning_summary if proposal else "",
            }
        )
    return rows


def generate_markdown_report(
    proposals: list[ProposedUpdate] | None = None,
    decisions: list[ReviewDecision] | None = None,
    settings: Settings | None = None,
) -> str:
    settings = settings or get_settings()
    proposals = proposals if proposals is not None else load_proposals_state(settings)
    decisions = decisions if decisions is not None else load_review_decisions(settings)
    audit_log = build_audit_log(proposals, decisions)
    if not settings.audit_log_path.exists():
        write_json(settings.audit_log_path, audit_log)

    approved_count = sum(1 for row in audit_log if row["decision"] == "approved")
    rejected_count = sum(1 for row in audit_log if row["decision"] == "rejected")
    lines = [
        "# Tariff Review Report",
        "",
        f"Generated at: {datetime.now(UTC).isoformat()}",
        "",
        "## Executive Summary",
        "",
        (
            f"The run produced {len(proposals)} structured tariff correction proposal(s). "
            f"{approved_count} approved update(s) are eligible for Excel mutation and "
            f"{rejected_count} rejected proposal(s) remain in audit history."
        ),
        (
            "Source conflicts were found in "
            f"{sum(1 for proposal in proposals if proposal.source_conflict_detected)} proposal(s), "
            "which should receive manual attention before operational rollout."
        ),
        "",
        "## Summary",
        "",
        f"- Proposals generated: {len(proposals)}",
        f"- Decisions captured: {len(decisions)}",
        f"- Approved updates applied: {approved_count}",
        f"- Rejected updates retained in audit only: {rejected_count}",
        "",
        "## Decisions",
        "",
        "| Pack ID | Pack | Field | Issue | Old Value | Proposed Value | Decision | Risk | Confidence |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in audit_log:
        lines.append(
            "| {pack_id} | {pack_name} | {field_name} | {issue_type} | {old_value} | "
            "{proposed_value} | {decision} | {risk_level} | {confidence_score} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Controls",
            "",
            "- Source Excel file is never mutated.",
            "- Only approved proposal fields are written to the output workbook.",
            "- Rejected proposals remain visible in the audit log for traceability.",
            "- Every row links the decision back to evidence sources and agent reasoning in `audit_log.json`.",
        ]
    )
    settings.report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(settings.report_path)


def load_audit_log(settings: Settings | None = None) -> list[dict[str, Any]]:
    settings = settings or get_settings()
    return read_json(settings.audit_log_path, [])


def _approved_proposals(
    proposals: list[ProposedUpdate],
    decisions: list[ReviewDecision],
) -> list[ProposedUpdate]:
    approved_ids = {decision.proposal_id for decision in decisions if decision.decision == "approved"}
    approved_keys = {
        (decision.pack_id, decision.field_name)
        for decision in decisions
        if decision.decision == "approved"
    }
    return [
        item
        for item in proposals
        if item.proposal_id in approved_ids or (item.pack_id, item.field_name) in approved_keys
    ]


def _mark_applied(
    proposals: list[ProposedUpdate],
    applied: list[ProposedUpdate],
    settings: Settings,
) -> None:
    applied_ids = {item.proposal_id for item in applied}
    for proposal in proposals:
        if proposal.proposal_id in applied_ids:
            proposal.status = "applied"
    write_json(settings.proposals_state_path, [item.model_dump(mode="json") for item in proposals])
