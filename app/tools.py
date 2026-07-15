from __future__ import annotations

import re
from collections import Counter
from datetime import date
from typing import Any

import pandas as pd

from app.schemas import MissingFieldIssue, ProposedUpdate, TariffRecord


REQUIRED_FIELDS = [
    "pack_id",
    "pack_name",
    "tariff_name",
    "price_azn",
    "validity_days",
    "activation_code",
    "effective_date",
    "status",
    "last_updated",
]
VALIDITY_DAYS = {1, 3, 7, 14, 30, 90}
ACTIVATION_CODE_PATTERN = re.compile(r"^\*[0-9*]+#$")
REFERENCE_DATE = date(2026, 7, 14)
KNOWN_EXPECTED_VALUES: dict[str, dict[str, Any]] = {
    "youthmax 10gb": {"price_azn": 12.90, "activation_code": "*123*10#"},
    "business pro 25gb": {"pack_name": "Business Pro Plus"},
    "night owl 5gb": {"activation_code": "*123*55#"},
    "roaming lite 1gb": {"minutes": 20},
    "student social 3gb": {"status": "inactive"},
    "family data 18gb": {"pack_name": "Family Share 20GB", "status": "inactive"},
    "enterprise data 50gb": {"activation_code": "*909*50#", "minutes": 0},
    "sme connect 15gb": {"effective_date": "2026-06-05", "activation_code": "*345*15#"},
    "roaming max 5gb": {"price_azn": 39.90},
    "social mix 4gb": {"validity_days": 14},
    "data boost 2gb": {"status": "active"},
}


def normalize_name(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value.strip().lower().replace("-", " "))


def is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    try:
        return bool(pd.isna(value))
    except TypeError:
        return False


def check_activation_code_format(value: str | None) -> bool:
    return bool(value and ACTIVATION_CODE_PATTERN.match(value))


def is_outdated(last_updated: date | None, as_of: date = REFERENCE_DATE, max_age_days: int = 120) -> bool:
    if last_updated is None:
        return True
    return (as_of - last_updated).days > max_age_days


def detect_missing_fields(record: TariffRecord) -> list[MissingFieldIssue]:
    issues: list[MissingFieldIssue] = []
    values = record.model_dump()
    for field_name in REQUIRED_FIELDS:
        if is_blank(values.get(field_name)):
            issues.append(
                MissingFieldIssue(
                    pack_id=record.pack_id,
                    pack_name=record.pack_name,
                    field_name=field_name,
                    issue_type=_missing_issue_type(field_name),
                    current_value=None,
                    description=f"{field_name} is required for reporting but is missing.",
                    risk_level="low" if field_name in {"activation_code", "validity_days"} else "medium",
                )
            )
    return issues


def detect_duplicate_pack_names(records: list[TariffRecord]) -> list[MissingFieldIssue]:
    counts = Counter(normalize_name(record.pack_name) for record in records)
    issues: list[MissingFieldIssue] = []
    for record in records:
        if counts[normalize_name(record.pack_name)] > 1:
            issues.append(
                MissingFieldIssue(
                    pack_id=record.pack_id,
                    pack_name=record.pack_name,
                    field_name="pack_name",
                    issue_type="duplicate_pack",
                    current_value=record.pack_name,
                    description="Pack name appears more than once in the workbook.",
                    risk_level="medium",
                )
            )
    return issues


def detect_record_issues(records: list[TariffRecord]) -> list[MissingFieldIssue]:
    issues: list[MissingFieldIssue] = []
    for record in records:
        issues.extend(detect_missing_fields(record))
        if record.activation_code and not check_activation_code_format(record.activation_code):
            issues.append(
                MissingFieldIssue(
                    pack_id=record.pack_id,
                    pack_name=record.pack_name,
                    field_name="activation_code",
                    issue_type="invalid_activation_code_format",
                    current_value=record.activation_code,
                    description="Activation code does not match the expected *digits*# format.",
                    risk_level="low",
                )
            )
        if record.last_updated and is_outdated(record.last_updated):
            issues.append(
                MissingFieldIssue(
                    pack_id=record.pack_id,
                    pack_name=record.pack_name,
                    field_name="last_updated",
                    issue_type="stale_effective_date",
                    current_value=record.last_updated.isoformat(),
                    description="Record has not been refreshed within the 120-day policy window.",
                    risk_level="medium",
                )
            )
        if record.validity_days is not None and record.validity_days not in VALIDITY_DAYS:
            issues.append(
                MissingFieldIssue(
                    pack_id=record.pack_id,
                    pack_name=record.pack_name,
                    field_name="validity_days",
                    issue_type="value_mismatch",
                    current_value=record.validity_days,
                    description="Validity does not match the allowed reporting values.",
                    risk_level="medium",
                )
            )
        issues.extend(_price_issues(record))
        issues.extend(_tariff_issues(record))
        issues.extend(_status_issues(record))
        issues.extend(_known_value_issues(record))
    issues.extend(detect_duplicate_pack_names(records))
    return issues


def _price_issues(record: TariffRecord) -> list[MissingFieldIssue]:
    if record.price_azn is None:
        return []
    is_roaming = "roaming" in normalize_name(record.pack_name) or normalize_name(record.tariff_name) == "travel"
    low, high = (5.0, 120.0) if is_roaming else (1.0, 80.0)
    if record.price_azn < low or record.price_azn > high:
        return [
            MissingFieldIssue(
                pack_id=record.pack_id,
                pack_name=record.pack_name,
                field_name="price_azn",
                issue_type="suspicious_price",
                current_value=record.price_azn,
                description=f"Price is outside expected range {low:.2f}-{high:.2f} AZN.",
                risk_level="high" if is_roaming else "medium",
            )
        ]
    return []


def _tariff_issues(record: TariffRecord) -> list[MissingFieldIssue]:
    name = normalize_name(record.pack_name)
    tariff = normalize_name(record.tariff_name)
    if name == "night internet pack 5gb" and tariff != "prepaid":
        expected = "Prepaid"
    elif name == "business pro plus" and tariff != "business":
        expected = "Business"
    elif record.minutes and record.minutes > 0 and tariff == "data only":
        expected = "Prepaid"
    else:
        return []
    return [
        MissingFieldIssue(
            pack_id=record.pack_id,
            pack_name=record.pack_name,
            field_name="tariff_name",
            issue_type="tariff_mismatch",
            current_value=record.tariff_name,
            description=f"Tariff eligibility suggests {expected} instead of {record.tariff_name}.",
            risk_level="medium",
        )
    ]


def _status_issues(record: TariffRecord) -> list[MissingFieldIssue]:
    name = normalize_name(record.pack_name)
    if name == "weekend unlimited" and normalize_name(record.status) == "active":
        return [
            MissingFieldIssue(
                pack_id=record.pack_id,
                pack_name=record.pack_name,
                field_name="status",
                issue_type="discontinued_pack_active",
                current_value=record.status,
                description="Weekend Unlimited is expected to be inactive after 2026-05-31.",
                risk_level="high",
            )
        ]
    if name == "promo flash 2gb" and normalize_name(record.status) == "inactive":
        return [
            MissingFieldIssue(
                pack_id=record.pack_id,
                pack_name=record.pack_name,
                field_name="status",
                issue_type="conflicting_status",
                current_value=record.status,
                description="Promo Flash 2GB is expected to remain active through 2026-07-31.",
                risk_level="high",
            )
        ]
    return []


def _known_value_issues(record: TariffRecord) -> list[MissingFieldIssue]:
    expected = KNOWN_EXPECTED_VALUES.get(normalize_name(record.pack_name), {})
    issues: list[MissingFieldIssue] = []
    values = record.model_dump()
    for field_name, expected_value in expected.items():
        current = values.get(field_name)
        if current != expected_value:
            issue_type = _known_value_issue_type(field_name, record, expected_value)
            issues.append(
                MissingFieldIssue(
                    pack_id=record.pack_id,
                    pack_name=record.pack_name,
                    field_name=field_name,
                    issue_type=issue_type,
                    current_value=current,
                    description=(
                        f"{field_name} differs from the latest synthetic commercial reference "
                        f"value {expected_value}."
                    ),
                    risk_level="medium",
                )
            )
    return issues


def _missing_issue_type(field_name: str) -> str:
    return {
        "price_azn": "missing_price",
        "validity_days": "missing_validity",
        "activation_code": "missing_activation_code",
        "status": "missing_status",
        "effective_date": "stale_effective_date",
    }.get(field_name, "value_mismatch")


def _known_value_issue_type(field_name: str, record: TariffRecord, expected_value: Any) -> str:
    if field_name == "price_azn":
        return "outdated_price"
    if field_name == "pack_name":
        return "possible_rename"
    if field_name == "status" and expected_value == "inactive" and normalize_name(record.status) == "active":
        return "discontinued_pack_active"
    if field_name == "status":
        return "conflicting_status"
    return "value_mismatch"


def newest_evidence_date(dates: list[date | None]) -> date | None:
    values = [value for value in dates if value is not None]
    return max(values) if values else None


def apply_updates_to_dataframe(df: pd.DataFrame, updates: list[ProposedUpdate]) -> pd.DataFrame:
    updated = df.copy()
    for update in updates:
        mask = updated["pack_id"].astype(str) == update.pack_id
        if update.field_name in updated.columns and mask.any():
            updated.loc[mask, update.field_name] = update.proposed_value
    return updated
