from typing import Annotated, Any

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from yetl.scraper.primitives import ScrapeBotModuleSetting


# =============== CHROME OPTION FIELD HELPERS ===============
def _chrome_argument(value: str) -> dict:
    return {"chrome_option": {"method": "add_argument", "value": value}}


def _chrome_experimental_option(key: str, value: Any) -> dict:
    return {"chrome_option": {"method": "add_experimental_option", "key": key, "value": value}}


# =============== SELENIUM BROWSER CONFIG ===============
class SeleniumBrowserConfig(ScrapeBotModuleSetting):
    # ===== WebDriverWait configurations
    TIMEOUT: Annotated[int, Field(ge=1, le=120)] = 10
    POLL_FREQUENCY: Annotated[float, Field(gt=0, le=10)] = 0.5

    # ===== WebDriverChrome Behavior Configurations
    TYPE_DELAY: Annotated[float, Field(ge=0, le=10)] = 0.0
    REDIRECT_CLICK_RETRY_LIMIT: Annotated[int, Field(ge=1, le=10)] = 3

    # ===== WebDriverChrome Options Configurations
    HEADLESS: Annotated[
        bool,
        Field(json_schema_extra=_chrome_argument("--headless=new")),
    ] = False
    DETACH: Annotated[
        bool,
        Field(json_schema_extra=_chrome_experimental_option("detach", True)),
    ] = False
    USER_AGENT: Annotated[
        str,
        Field(json_schema_extra=_chrome_argument("--user-agent={value}")),
    ] = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    )

    model_config = SettingsConfigDict(
        env_prefix="SELENIUM_",
        extra="ignore",
    )
