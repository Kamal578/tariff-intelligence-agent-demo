from app.excel_io import load_tariff_records
from app.tools import check_activation_code_format, detect_record_issues


def test_activation_code_format() -> None:
    assert check_activation_code_format("*123*10#")
    assert not check_activation_code_format("5555")


def test_detects_expected_sample_issues() -> None:
    records = load_tariff_records("data/input/tariff_packs.xlsx")
    issues = detect_record_issues(records)
    keys = {(issue.pack_id, issue.field_name, issue.issue_type) for issue in issues}

    assert ("PK001", "price_azn", "outdated_price") in keys
    assert ("PK003", "activation_code", "missing_activation_code") in keys
    assert ("PK005", "status", "discontinued_pack_active") in keys
    assert ("PK024", "price_azn", "suspicious_price") in keys
