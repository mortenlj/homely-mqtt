from enum import Enum

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class Mode(str, Enum):
    DEBUG = "Debug"
    RELEASE = "Release"


class HomelySettings(BaseModel):
    username: str
    password: str
    location: str = "Hjemme"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="HOMELY_MQTT__", env_file=".env", env_nested_delimiter="__")

    mode: Mode = Mode.DEBUG
    bind_address: str = "127.0.0.1"
    port: int = 3000

    homely: HomelySettings

    @property
    def debug(self):
        return self.mode == Mode.DEBUG


settings = Settings()
