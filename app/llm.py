from __future__ import annotations

import json
import re
from typing import Any

from pydantic import ValidationError

from app.config import Settings
from app.schemas import Evidence, MissingFieldIssue, ProposedUpdate, TariffRecord
from app.tools import normalize_name


FIELD_KNOWLEDGE: dict[str, dict[str, Any]] = {
    "youthmax 10gb": {
        "price_azn": 12.90,
        "validity_days": 30,
        "activation_code": "*123*10#",
        "effective_date": "2026-06-01",
        "last_updated": "2026-06-10",
    },
    "business pro 25gb": {
        "pack_name": "Business Pro Plus",
        "data_gb": 25,
        "price_azn": 29.90,
        "activation_code": "*234*25#",
        "last_updated": "2026-06-10",
    },
    "business pro plus": {
        "data_gb": 25,
        "price_azn": 29.90,
        "activation_code": "*234*25#",
        "last_updated": "2026-06-10",
    },
    "night internet pack 5gb": {
        "tariff_name": "Prepaid",
        "activation_code": "*555*5#",
        "price_azn": 4.90,
        "validity_days": 7,
        "last_updated": "2026-06-10",
    },
    "night owl 5gb": {
        "activation_code": "*123*55#",
        "price_azn": 4.90,
        "validity_days": 7,
        "last_updated": "2026-06-19",
    },
    "student social 3gb": {
        "validity_days": 14,
        "activation_code": "*321*3#",
        "status": "inactive",
        "last_updated": "2026-05-15",
    },
    "family data 18gb": {
        "pack_name": "Family Share 20GB",
        "status": "inactive",
        "data_gb": 20,
        "activation_code": "*456*20#",
        "last_updated": "2026-06-24",
    },
    "family share 20gb": {
        "price_azn": 24.90,
        "validity_days": 30,
        "activation_code": "*456*20#",
        "last_updated": "2026-06-24",
    },
    "executive voice 1000": {
        "price_azn": 19.90,
        "validity_days": 30,
        "activation_code": "*700*1000#",
        "last_updated": "2026-06-21",
    },
    "sme connect 15gb": {
        "effective_date": "2026-06-05",
        "activation_code": "*345*15#",
        "price_azn": 18.90,
        "last_updated": "2026-06-21",
    },
    "enterprise data 50gb": {
        "activation_code": "*909*50#",
        "minutes": 0,
        "last_updated": "2026-06-19",
    },
    "weekend turbo 8gb": {
        "price_azn": 8.90,
        "last_updated": "2026-06-04",
    },
    "social mix 4gb": {
        "validity_days": 14,
        "activation_code": "*222*4#",
        "last_updated": "2026-06-26",
    },
    "data boost 2gb": {
        "status": "active",
        "price_azn": 2.90,
        "validity_days": 3,
        "last_updated": "2026-06-26",
    },
    "weekend unlimited": {
        "status": "inactive",
        "last_updated": "2026-06-18",
    },
    "data boost 15gb": {
        "data_gb": 15,
        "activation_code": "*777*15#",
        "price_azn": 14.90,
        "validity_days": 30,
        "last_updated": "2026-06-25",
    },
    "roaming lite 1gb": {
        "price_azn": 7.50,
        "minutes": 20,
        "activation_code": "*123*77#",
        "last_updated": "2026-06-28",
    },
    "roaming max 5gb": {
        "price_azn": 39.90,
        "activation_code": "*909*5#",
        "last_updated": "2026-06-27",
    },
    "family share 40gb": {
        "effective_date": "2026-06-01",
        "last_updated": "2026-06-01",
    },
    "promo flash 2gb": {
        "status": "active",
        "price_azn": 2.90,
        "validity_days": 3,
        "last_updated": "2026-06-18",
    },
    "mega stream 50gb": {
        "price_azn": 49.90,
        "minutes": 0,
        "last_updated": "2026-06-25",
    },
    "voice plus 100": {
        "tariff_name": "Prepaid",
        "last_updated": "2026-05-01",
    },
}


class GeminiProvider:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @property
    def available(self) -> bool:
        return bool(self.settings.gemini_api_key)

    def propose_update(
        self,
        record: TariffRecord,
        issue: MissingFieldIssue,
        evidence: list[Evidence],
    ) -> tuple[ProposedUpdate, str]:
        if not self.available:
            return fallback_update(record, issue, evidence), "fallback"
        try:
            proposal = self._call_gemini(record, issue, evidence)
            return proposal, "gemini"
        except Exception:
            return fallback_update(record, issue, evidence), "fallback"

    def _call_gemini(
        self,
        record: TariffRecord,
        issue: MissingFieldIssue,
        evidence: list[Evidence],
    ) -> ProposedUpdate:
        from google import genai

        client = genai.Client(api_key=self.settings.gemini_api_key)
        response = client.models.generate_content(
            model=self.settings.gemini_model,
            contents=_build_prompt(record, issue, evidence),
        )
        payload = _extract_json(response.text or "")
        try:
            proposal = ProposedUpdate.model_validate(payload)
        except ValidationError as exc:
            raise ValueError("Gemini response did not match ProposedUpdate schema") from exc
        return proposal


def _build_prompt(
    record: TariffRecord,
    issue: MissingFieldIssue,
    evidence: list[Evidence],
) -> str:
    schema = ProposedUpdate.model_json_schema()
    evidence_text = "\n\n".join(
        f"Source: {item.source_id} ({item.source_type})\nDate: {item.timestamp}\nTitle: {item.title_or_subject}\nExcerpt: {item.excerpt}"
        for item in evidence
    )
    return f"""
You are a telecom revenue-assurance assistant.
Return only valid JSON matching this schema:
{json.dumps(schema)}

Rules:
- Propose exactly one update for the supplied issue.
- Do not invent evidence. Use the supplied sources.
- Set requires_human_review to true for every proposal.
- Use status "new" unless evidence is weak, then use "needs_review".

Record:
{record.model_dump_json()}

Issue:
{issue.model_dump_json()}

Evidence:
{evidence_text}
"""


def _extract_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned)
        cleaned = re.sub(r"```$", "", cleaned).strip()
    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in model response")
    return json.loads(match.group(0))


def fallback_update(
    record: TariffRecord,
    issue: MissingFieldIssue,
    evidence: list[Evidence],
) -> ProposedUpdate:
    pack_key = normalize_name(record.pack_name)
    knowledge = FIELD_KNOWLEDGE.get(pack_key, {})
    proposed_value = knowledge.get(issue.field_name)
    field_name = issue.field_name

    if proposed_value is None:
        field_name, proposed_value = _fallback_field_and_value(record, issue, knowledge, evidence)

    confidence = _fallback_confidence(issue, proposed_value, evidence)
    status = "new" if confidence >= 0.72 and issue.risk_level != "high" else "needs_review"
    conflict = detect_source_conflict(evidence)
    return ProposedUpdate(
        proposal_id=f"{record.pack_id}-{field_name}",
        pack_id=record.pack_id,
        pack_name=record.pack_name,
        field_name=field_name,
        old_value=getattr(record, field_name, issue.current_value),
        proposed_value=proposed_value if proposed_value is not None else issue.current_value,
        issue_type=issue.issue_type,
        confidence_score=confidence,
        risk_level=issue.risk_level,
        status=status,
        evidence_sources=evidence[:5],
        reasoning_summary=_fallback_reasoning(record, issue, proposed_value, evidence),
        source_conflict_detected=conflict,
        source_freshness_summary=freshness_summary(evidence),
        decision_basis=_decision_basis(issue, evidence, conflict),
        requires_human_review=True,
    )


def _fallback_field_and_value(
    record: TariffRecord,
    issue: MissingFieldIssue,
    knowledge: dict[str, Any],
    evidence: list[Evidence],
) -> tuple[str, Any]:
    if issue.issue_type in {"invalid_activation_code_format", "missing_activation_code"} and "activation_code" in knowledge:
        return "activation_code", knowledge["activation_code"]
    if issue.issue_type in {"suspicious_price", "missing_price", "outdated_price"} and "price_azn" in knowledge:
        return "price_azn", knowledge["price_azn"]
    if issue.issue_type == "tariff_mismatch" and "tariff_name" in knowledge:
        return "tariff_name", knowledge["tariff_name"]
    if issue.issue_type in {"conflicting_status", "discontinued_pack_active", "missing_status"} and "status" in knowledge:
        return "status", knowledge["status"]
    if issue.issue_type == "stale_effective_date":
        if issue.field_name in knowledge:
            return issue.field_name, knowledge[issue.field_name]
        latest_date = max((item.timestamp.date() for item in evidence), default=None)
        return "last_updated", latest_date.isoformat() if latest_date else record.last_updated
    if issue.issue_type == "duplicate_pack":
        return "pack_name", record.pack_name
    return issue.field_name, knowledge.get(issue.field_name, issue.current_value)


def _fallback_confidence(
    issue: MissingFieldIssue,
    proposed_value: Any,
    evidence: list[Evidence],
) -> float:
    if proposed_value is None:
        return 0.35
    base = 0.82 if evidence else 0.62
    if issue.risk_level == "high":
        base -= 0.18
    if issue.issue_type == "duplicate_pack":
        base = 0.45
    return max(0.0, min(0.95, base))


def _fallback_reasoning(
    record: TariffRecord,
    issue: MissingFieldIssue,
    proposed_value: Any,
    evidence: list[Evidence],
) -> str:
    if proposed_value is None:
        return f"{issue.description} No deterministic correction was found for {record.pack_name}."
    sources = ", ".join(item.source_id for item in evidence[:2]) or "built-in demo rules"
    return (
        f"{issue.description} Proposed value is based on the latest matching synthetic "
        f"knowledge for {record.pack_name}; primary evidence: {sources}."
    )


def detect_source_conflict(evidence: list[Evidence]) -> bool:
    statuses = {item.document_status for item in evidence}
    return bool({"approved", "deprecated"}.issubset(statuses) or {"approved", "draft"}.issubset(statuses))


def freshness_summary(evidence: list[Evidence]) -> str:
    if not evidence:
        return "No matching mock source evidence was retrieved."
    newest = max(item.timestamp for item in evidence)
    oldest = min(item.timestamp for item in evidence)
    return f"Newest evidence is {newest.date().isoformat()}; oldest retrieved evidence is {oldest.date().isoformat()}."


def _decision_basis(issue: MissingFieldIssue, evidence: list[Evidence], conflict: bool) -> str:
    approved = [item.source_id for item in evidence if item.document_status == "approved"]
    if conflict:
        return f"Conflicting mock sources were found; prefer newer approved sources: {', '.join(approved[:3]) or 'none'}."
    if approved:
        return f"Proposal is based on approved or high-priority mock source evidence: {', '.join(approved[:3])}."
    return f"Proposal is based on deterministic validation for issue type {issue.issue_type} with partial source support."
