from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


load_dotenv()


class Settings(BaseSettings):
    """Runtime settings for local demo paths and optional Gemini access."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = Field(default="local", alias="APP_ENV")
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_MODEL")
    chroma_dir: Path = Field(default=Path("data/chroma"), alias="CHROMA_DIR")
    input_excel_path: Path = Field(
        default=Path("data/input/tariff_packs.xlsx"), alias="INPUT_EXCEL_PATH"
    )
    output_dir: Path = Field(default=Path("data/output"), alias="OUTPUT_DIR")
    knowledge_base_dir: Path = Path("data/knowledge_base")

    @property
    def records_state_path(self) -> Path:
        return self.output_dir / "records.json"

    @property
    def proposals_state_path(self) -> Path:
        return self.output_dir / "proposals.json"

    @property
    def review_state_path(self) -> Path:
        return self.output_dir / "review_decisions.json"

    @property
    def audit_log_path(self) -> Path:
        return self.output_dir / "audit_log.json"

    @property
    def report_path(self) -> Path:
        return self.output_dir / "review_report.md"

    @property
    def updated_excel_path(self) -> Path:
        return self.output_dir / "updated_tariff_packs.xlsx"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    return settings
