from pathlib import Path
from typing import Any

import pandas as pd

from app.schemas import TariffRecord


DATE_COLUMNS = {"effective_date", "last_updated"}


def _clean_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    if hasattr(value, "date"):
        return value.date()
    return value


def load_tariff_dataframe(path: Path | str) -> pd.DataFrame:
    df = pd.read_excel(path, engine="openpyxl")
    for column in DATE_COLUMNS.intersection(df.columns):
        df[column] = pd.to_datetime(df[column], errors="coerce").dt.date
    return df


def load_tariff_records(path: Path | str) -> list[TariffRecord]:
    df = load_tariff_dataframe(path)
    records: list[TariffRecord] = []
    for raw in df.to_dict(orient="records"):
        cleaned = {key: _clean_value(value) for key, value in raw.items()}
        records.append(TariffRecord.model_validate(cleaned))
    return records


def write_tariff_dataframe(df: pd.DataFrame, path: Path | str) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="tariff_packs")
        worksheet = writer.sheets["tariff_packs"]
        for column_cells in worksheet.columns:
            header = column_cells[0].value or ""
            max_len = max(len(str(cell.value or "")) for cell in column_cells)
            worksheet.column_dimensions[column_cells[0].column_letter].width = max(
                len(str(header)) + 2, min(max_len + 2, 48)
            )
    return output_path
