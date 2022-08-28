from enum import Enum

from pydantic import BaseSettings


class Mode(str, Enum):
    DEBUG = "Debug"
    RELEASE = "Release"

    def __new__(cls, value):
        return super().__new__(cls, value.lower())


class Settings(BaseSettings):
    class Config:
        env_prefix = "HOMELY_MQTT_"
        env_file = ".env"

    mode: Mode = Mode.DEBUG
    bind_address: str = "127.0.0.1"
    port: int = 3000

    homely_username: str
    homely_password: str

    @property
    def debug(self):
        return self.mode == Mode.DEBUG


settings = Settings()
