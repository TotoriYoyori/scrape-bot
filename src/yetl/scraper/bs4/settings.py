from pydantic_settings import SettingsConfigDict

from yetl.scraper.primitives import ScrapeBotModuleSetting


# =============== BEAUTIFUL SOUP CONFIG ===============
class BeautifulSoupConfig(ScrapeBotModuleSetting):
    PARSER: str = "html.parser"
    TEXT_SEPARATOR: str = " "
    STRIP_TEXT: bool = True

    model_config = SettingsConfigDict(
        env_prefix="BS4_",
        extra="ignore",
    )
