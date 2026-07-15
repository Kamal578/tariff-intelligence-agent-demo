import pytest
from pydantic import ValidationError

from datetime import UTC, datetime

from app.schemas import Evidence, ProposedUpdate, TariffRecord


def test_tariff_record_requires_pack_identity() -> None:
    record = TariffRecord(pack_id="PK001", pack_name="YouthMax 10GB")
    assert record.pack_id == "PK001"
    assert record.pack_name == "YouthMax 10GB"


def test_proposed_update_confidence_is_bounded() -> None:
    evidence = Evidence(
        source_id="CONF-001",
        source_type="confluence",
        title_or_subject="YouthMax 10GB Approved Commercial Card",
        author_or_owner="Youth Products",
        timestamp=datetime(2026, 6, 12, tzinfo=UTC),
        fake_url="https://confluence.demo.local/pages/CONF-001",
        excerpt="Approved values for YouthMax 10GB.",
        relevance_score=0.9,
        source_priority="high",
        document_status="approved",
        matched_terms=["youthmax"],
    )
    with pytest.raises(ValidationError):
        ProposedUpdate(
            proposal_id="PK001-price_azn",
            pack_id="PK001",
            pack_name="YouthMax 10GB",
            field_name="price_azn",
            old_value=None,
            proposed_value=12.9,
            issue_type="missing_price",
            confidence_score=1.2,
            evidence_sources=[evidence],
            reasoning_summary="Out of range confidence should fail validation.",
            risk_level="low",
            requires_human_review=True,
        )
