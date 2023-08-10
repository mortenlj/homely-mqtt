from enum import Enum
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Mode(str, Enum):
    DEBUG = "Debug"
    RELEASE = "Release"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="HOMELY_MQTT_", env_file=".env")

    mode: Mode = Mode.DEBUG
    bind_address: str = "127.0.0.1"
    port: int = 3000

    homely_username: str
    homely_password: str

    @property
    def debug(self):
        return self.mode == Mode.DEBUG


settings = Settings()
