import logging

from pydantic import field_validator
from pydantic_settings import SettingsConfigDict

from yetl.scraper.logger.palette import LOGGER_PALETTE_REGISTRY
from yetl.scraper.primitives import ScrapeBotModuleSetting


LOGGER_LEVELS: dict[str, int] = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

# =============== LOGGER CONFIG ===============
class LoggerConfig(ScrapeBotModuleSetting):
    NAME: str = "ScrapeBot"
    LEVEL: str = "DEBUG"
    PROPAGATE: bool = False
    PALETTE: str = "basic"
    FORMAT_TEMPLATE: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    model_config = SettingsConfigDict(
        env_prefix="LOGGER_",
        extra="ignore",
    )

    @field_validator("LEVEL", mode="before")
    @classmethod
    def validate_level(cls, value: str) -> str:
        normalized = value.strip().upper()
        if normalized not in LOGGER_LEVELS:
            raise ValueError(
                f"'{value}' is not a valid logger level. "
                f"Must be one of: {sorted(LOGGER_LEVELS)}"
            )

        return normalized

    @field_validator("PALETTE")
    @classmethod
    def validate_palette(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in LOGGER_PALETTE_REGISTRY:
            raise ValueError(
                f"'{value}' is not a valid logger palette. "
                f"Must be one of: {sorted(LOGGER_PALETTE_REGISTRY)}"
            )

        return normalized
