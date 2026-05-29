from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


# =============== NOTIFICATION SETTINGS ===============
class NotificationSettings(BaseSettings):
    SENDER_EMAIL: str
    RECEIVER_EMAIL: str
    PASSWORD: str

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_prefix="NOTIFICATION_",
        extra="ignore",
    )
