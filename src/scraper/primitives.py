from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# =============== BASE CLASS FOR SCRAPE BOT MODULE SETTINGS ===============
class ScrapeBotModuleSetting(BaseSettings):
    """Shared base class for scraper module settings.

    Attributes:
        model_config: Tells Pydantic to read settings from the project ``.env``
            file and ignore unrelated environment variables.

    Example:
        >>> class ExampleSettings(ScrapeBotModuleSetting):
        ...     enabled: bool = True
        >>> settings = ExampleSettings()
        >>> assert settings.enabled is True
    """

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# =============== BASE CLASS FOR INSTALLABLE SCRAPE BOT MODULES ===============
class ScrapeBotModule:
    """Module that can be installed onto a ScrapeBot."""

    name: str


# =============== ROUTINE CONTRACTS AND RECORD MODELS ===============
class ScrapeBotRoutine(Protocol):
    """Protocol for scrape routines executed by a ScrapeBot."""

    def execute(self, bot) -> None:
        """Run the routine with the provided ScrapeBot."""


class ScrapeBotRoutineRecord(BaseModel):
    """Base model for records produced by scrape routines.

    Use this as the parent class for routine output models that capture raw
    scraped values. It keeps those records lightweight by:

    * Ignoring unexpected fields.
    * Making records immutable after creation.
    * Normalizing copied-web Unicode characters.
    * Normalizing string whitespace.
    * Converting blank strings to ``None``.

    Examples:
        >>> class ExampleRecord(ScrapeBotRoutineRecord):
        ...     title: str | None
        ...     author: str | None
        >>> record = ExampleRecord(
        ...     title="  Ｔｈｅ\\xa0\\u200bExample\\nBook  ",
        ...     author="   ",
        ...     ignored_field="not stored",
        ... )
        >>> assert record.title == "The Example Book"
        >>> assert record.author is None
        >>> assert not hasattr(record, "ignored_field")
    """

    model_config = ConfigDict(extra="ignore", frozen=True)

    @field_validator("*", mode="before")
    @classmethod
    def normalize_text_characters(cls, value: Any) -> Any:
        if not isinstance(value, str):
            return value

        normalized = unicodedata.normalize("NFKC", value)
        normalized = normalized.replace("\xa0", " ")
        return normalized.translate(str.maketrans("", "", "\u200b\u200c\u200d\ufeff"))

    @field_validator("*", mode="before")
    @classmethod
    def normalize_whitespace(cls, value: Any) -> Any:
        if not isinstance(value, str):
            return value

        return re.sub(r"\s+", " ", value).strip()

    @field_validator("*", mode="after")
    @classmethod
    def nullify_empty_string(cls, value: Any) -> Any:
        if value == "":
            return None

        return value
