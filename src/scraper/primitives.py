from __future__ import annotations

from pathlib import Path
from typing import Protocol

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


# =============== PROTOCOL FOR SCRAPE BOT ROUTINES ===============
class ScrapeBotRoutine(Protocol):
    """Protocol for scrape routines executed by a ScrapeBot."""

    def execute(self, bot) -> None:
        """Run the routine with the provided ScrapeBot."""
