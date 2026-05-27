from typing import Annotated

from pydantic import Field, model_validator
from pydantic_settings import SettingsConfigDict

from yetl.scraper.primitives import ScrapeBotModuleSetting


# =============== TIMING CONFIG ===============
class TimingConfig(ScrapeBotModuleSetting):
    # ===== Sleep configurations
    SLEEP_BASE: Annotated[float, Field(ge=0, le=60)] = 1.0
    SLEEP_MIN: Annotated[float, Field(ge=0, le=60)] = 0.5
    SLEEP_MAX: Annotated[float, Field(ge=0, le=60)] = 1.5

    # ===== Retry configurations
    RETRY_ATTEMPTS: Annotated[int, Field(ge=1, le=5)] = 2
    RETRY_DELAY_SECONDS: Annotated[float, Field(ge=0, le=60)] = 1.0

    model_config = SettingsConfigDict(
        env_prefix="TIMING_",
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_smart_sleep_bounds(self) -> "TimingConfig":
        if self.SLEEP_MAX < self.SLEEP_MIN:
            raise ValueError("SLEEP_MAX must be greater than or equal to SLEEP_MIN.")

        return self
