from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class SnowflakeSettings(BaseSettings):
    SNOWFLAKE_USERNAME: str
    SNOWFLAKE_PASSWORD: str
    SNOWFLAKE_ACCOUNT: str

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
    )
