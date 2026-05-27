from pydantic import Field
from pydantic_settings import SettingsConfigDict

from src.scraper.primitives import ScrapeBotModuleSetting


class AudibleRoutineSettings(ScrapeBotModuleSetting):
    SKIP_MAP: dict[str, list[int]] = Field(
        default_factory=lambda: {
            "Biographies & Memoirs": [2, 5],
            "Literature & Fiction": [10, 11],
            "History": [5],
            "Mystery, Thriller & Suspense": [3],
            "Romance": [1, 7, 8],
            "Sports & Outdoors": [0, 3, 23],
        }
    )
    PAGE_RETRY_DELAY: int = 2
    PAGE_LOAD_SENTINEL: str = "adbl-impression-container"

    model_config = SettingsConfigDict(
        env_prefix="AUDIBLE_ROUTINE_",
        extra="ignore",
    )
