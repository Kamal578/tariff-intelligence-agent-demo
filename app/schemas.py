from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


ProposalStatus = Literal["proposed", "approved", "rejected", "needs_review"]
RiskLevel = Literal["low", "medium", "high"]
DecisionValue = Literal["approved", "rejected"]


class TariffRecord(BaseModel):
    pack_id: str
    pack_name: str
    tariff_name: str | None = None
    price_azn: float | None = None
    validity_days: int | None = None
    data_gb: float | None = None
    minutes: int | None = None
    sms: int | None = None
    activation_code: str | None = None
    effective_date: date | None = None
    status: str | None = None
    last_updated: date | None = None
    source_note: str | None = None

    @field_validator("pack_id", "pack_name")
    @classmethod
    def required_text(cls, value: str) -> str:
        if not value or not str(value).strip():
            raise ValueError("required text cannot be blank")
        return str(value).strip()


class MissingFieldIssue(BaseModel):
    pack_id: str
    pack_name: str
    field_name: str
    issue_type: Literal[
        "missing_field",
        "invalid_activation_code",
        "outdated_record",
        "duplicate_pack_name",
        "price_anomaly",
        "tariff_mismatch",
        "status_conflict",
        "value_mismatch",
    ]
    current_value: Any = None
    description: str
    risk_level: RiskLevel = "medium"


class RetrievedEvidence(BaseModel):
    source: str
    content: str
    relevance_score: float = Field(ge=0, le=1)
    evidence_date: date | None = None


class ProposedUpdate(BaseModel):
    pack_id: str
    field_name: str
    old_value: Any = None
    proposed_value: Any
    confidence_score: float = Field(ge=0, le=1)
    status: ProposalStatus = "proposed"
    evidence_sources: list[str] = Field(default_factory=list)
    reasoning_summary: str
    risk_level: RiskLevel = "medium"
    requires_human_review: bool = True


class ReviewDecision(BaseModel):
    pack_id: str
    field_name: str
    decision: DecisionValue
    reviewer: str = "demo_analyst"
    reasoning: str = ""
    decided_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ProcessingResult(BaseModel):
    records: list[TariffRecord]
    issues: list[MissingFieldIssue]
    proposals: list[ProposedUpdate]
    mode: Literal["gemini", "fallback", "mixed"] = "fallback"
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
