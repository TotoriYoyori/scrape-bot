from __future__ import annotations

import datetime as dt
from pathlib import Path

from pydantic import Field, ValidationInfo, field_validator
from pydantic_settings import SettingsConfigDict

from yetl.scraper.primitives import ScrapeBotModuleSetting

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class CsvWriterConfig(ScrapeBotModuleSetting):
    LOCATION: Path = Field(default_factory=lambda: PROJECT_ROOT / "output")
    OUTPUT_PATH: Path = Field(default=None, validate_default=True)

    @field_validator("OUTPUT_PATH", mode="before")
    @classmethod
    def generate_output_path(
        cls, value: Path | str | None, info: ValidationInfo
    ) -> Path:
        if value is not None:
            return Path(value)

        location = Path(info.data.get("LOCATION", PROJECT_ROOT / "output"))
        today = dt.date.today().strftime("%Y%m%d")

        return location / f"export_audible_dirty_{today}.csv"

    model_config = SettingsConfigDict(
        env_prefix="WRITER_",
        extra="ignore",
    )
