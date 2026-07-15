from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


ProposalStatus = Literal["new", "proposed", "needs_review", "approved", "rejected", "applied", "superseded"]
RiskLevel = Literal["low", "medium", "high"]
DecisionValue = Literal["approved", "rejected"]
SourceType = Literal["confluence", "wiki", "email"]
AnalysisMode = Literal["preview", "gemini"]
ProcessingMode = Literal["preview", "gemini", "fallback", "mixed"]
AnalysisJobStatus = Literal["queued", "running", "completed", "failed"]
IssueType = Literal[
    "missing_price",
    "missing_validity",
    "missing_activation_code",
    "invalid_activation_code_format",
    "outdated_price",
    "possible_rename",
    "discontinued_pack_active",
    "duplicate_pack",
    "suspicious_price",
    "stale_effective_date",
    "conflicting_status",
    "missing_status",
    "tariff_mismatch",
    "value_mismatch",
]


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
    issue_type: IssueType
    current_value: Any = None
    description: str
    risk_level: RiskLevel = "medium"


class Evidence(BaseModel):
    source_id: str
    source_type: SourceType
    title_or_subject: str
    author_or_owner: str | None = None
    timestamp: datetime
    fake_url: str
    excerpt: str
    relevance_score: float = Field(ge=0, le=1)
    source_priority: Literal["high", "medium", "low"] = "medium"
    document_status: Literal["approved", "deprecated", "draft", "n/a"] = "n/a"
    matched_terms: list[str] = Field(default_factory=list)


class RetrievedEvidence(BaseModel):
    source: str
    content: str
    relevance_score: float = Field(ge=0, le=1)
    evidence_date: date | None = None


class ProposedUpdate(BaseModel):
    proposal_id: str
    pack_id: str
    pack_name: str
    field_name: str
    old_value: Any = None
    proposed_value: Any
    issue_type: IssueType
    confidence_score: float = Field(ge=0, le=1)
    risk_level: RiskLevel = "medium"
    status: ProposalStatus = "proposed"
    evidence_sources: list[Evidence] = Field(default_factory=list)
    reasoning_summary: str
    source_conflict_detected: bool = False
    source_freshness_summary: str = ""
    decision_basis: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    requires_human_review: bool = True


class ReviewDecision(BaseModel):
    proposal_id: str | None = None
    pack_id: str
    field_name: str
    decision: DecisionValue
    reviewer: str = "demo_analyst"
    reasoning: str = ""
    decided_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ProcessRequest(BaseModel):
    mode: AnalysisMode = "preview"


class ProcessingResult(BaseModel):
    records: list[TariffRecord]
    issues: list[MissingFieldIssue]
    proposals: list[ProposedUpdate]
    mode: ProcessingMode = "preview"
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ProcessSummary(BaseModel):
    records: int = 0
    issues: int = 0
    proposals: int = 0
    high_risk_proposals: int = 0
    source_conflicts: int = 0
    mode: ProcessingMode = "preview"
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AnalysisJob(BaseModel):
    job_id: str
    requested_mode: AnalysisMode = "preview"
    status: AnalysisJobStatus = "queued"
    stage: str = "Queued"
    progress: int = Field(default=0, ge=0, le=100)
    actual_mode: ProcessingMode | None = None
    summary: ProcessSummary | None = None
    error: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    finished_at: datetime | None = None
