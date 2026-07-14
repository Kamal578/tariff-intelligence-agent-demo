import pytest
from pydantic import ValidationError

from app.schemas import ProposedUpdate, TariffRecord


def test_tariff_record_requires_pack_identity() -> None:
    record = TariffRecord(pack_id="PK001", pack_name="YouthMax 10GB")
    assert record.pack_id == "PK001"
    assert record.pack_name == "YouthMax 10GB"


def test_proposed_update_confidence_is_bounded() -> None:
    with pytest.raises(ValidationError):
        ProposedUpdate(
            pack_id="PK001",
            field_name="price_azn",
            old_value=None,
            proposed_value=12.9,
            confidence_score=1.2,
            evidence_sources=["confluence_tariff_updates.md"],
            reasoning_summary="Out of range confidence should fail validation.",
            risk_level="low",
            requires_human_review=True,
        )
