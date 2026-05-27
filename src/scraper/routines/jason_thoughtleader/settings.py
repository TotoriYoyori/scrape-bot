from pydantic import Field
from pydantic_settings import SettingsConfigDict

from src.scraper.primitives import ScrapeBotModuleSetting


class JasonThoughtleaderSettings(ScrapeBotModuleSetting):
    HOME_URL: str = "https://www.linkedin.com/"
    EMAIL: str
    PASSWORD: str
    POST_TEXT: str = Field(
        default=(
            "Leadership is about turning uncertainty into alignment, "
            "one authentic conversation at a time."
        )
    )
    FOLLOW_LIMIT: int = Field(default=8, ge=0)

    model_config = SettingsConfigDict(
        env_prefix="JASON_",
        extra="ignore",
    )
