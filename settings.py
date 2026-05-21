from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# =============== SETTINGS ===============
class Settings(BaseSettings):
    # ----- Webscraping
    AUDIBLE_BASE_URL: str = "https://www.audible.com/search"

    # ----- ETL

    # ----- Snowflake Credentials
    SNOWFLAKE_USERNAME: str
    SNOWFLAKE_PASSWORD: str
    SNOWFLAKE_ACCOUNT: str

    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent / 'settings.env',
    )


# =============== GLOBAL APP INSTANCE ===============
settings = Settings()
