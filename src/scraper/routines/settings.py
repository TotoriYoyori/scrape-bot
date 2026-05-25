from pydantic import Field
from pydantic_settings import SettingsConfigDict

from src.scraper.primitives import ScrapeBotModuleSetting


class AudibleRoutineSettings(ScrapeBotModuleSetting):
    CSV_FIELDNAMES: list[str] = Field(
        default_factory=lambda: [
            "name",
            "author",
            "narrator",
            "runtime",
            "release_date",
            "language",
            "stars",
            "price",
            "category",
            "subcategory",
        ]
    )
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

    model_config = SettingsConfigDict(
        env_prefix="AUDIBLE_ROUTINE_",
        extra="ignore",
    )


routine_settings = AudibleRoutineSettings()
