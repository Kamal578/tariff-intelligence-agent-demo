from pathlib import Path

from openpyxl import load_workbook

from app.config import Settings
from app.pipeline import ingest_knowledge, process_tariffs
from app.reporting import apply_approved_updates, load_audit_log
from app.review_store import save_review_decision
from app.schemas import ReviewDecision


def make_settings(tmp_path: Path) -> Settings:
    return Settings(
        INPUT_EXCEL_PATH=Path("data/input/tariff_packs.xlsx"),
        OUTPUT_DIR=tmp_path / "output",
        CHROMA_DIR=tmp_path / "chroma",
        GEMINI_API_KEY="",
    )


def test_pipeline_generates_fallback_proposals(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    ingest_result = ingest_knowledge(settings)
    result = process_tariffs(settings)

    assert ingest_result["indexed_chunks"] > 0
    assert result.mode == "fallback"
    assert len(result.records) == 15
    assert any(
        proposal.pack_id == "PK001"
        and proposal.field_name == "price_azn"
        and proposal.proposed_value == 12.9
        for proposal in result.proposals
    )


def test_apply_approved_updates_only_mutates_approved_fields(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    process_tariffs(settings)
    save_review_decision(
        ReviewDecision(
            pack_id="PK001",
            field_name="price_azn",
            decision="approved",
            reviewer="pytest",
            reasoning="Approved sample price correction.",
        ),
        settings,
    )
    save_review_decision(
        ReviewDecision(
            pack_id="PK001",
            field_name="activation_code",
            decision="rejected",
            reviewer="pytest",
            reasoning="Rejected sample activation code correction.",
        ),
        settings,
    )

    result = apply_approved_updates(settings)
    workbook = load_workbook(result["output_excel"], read_only=True, data_only=True)
    sheet = workbook["tariff_packs"]
    headers = [cell.value for cell in next(sheet.iter_rows(min_row=1, max_row=1))]
    price_idx = headers.index("price_azn")
    activation_idx = headers.index("activation_code")
    row = next(row for row in sheet.iter_rows(min_row=2, values_only=True) if row[0] == "PK001")

    assert row[price_idx] == 12.9
    assert row[activation_idx] == "*123*09#"
    assert Path(result["audit_log"]).exists()
    assert Path(result["report"]).exists()
    assert {entry["decision"] for entry in load_audit_log(settings)} == {"approved", "rejected"}
