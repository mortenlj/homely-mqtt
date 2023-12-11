from enum import Enum

from pydantic import BaseModel, FilePath, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Mode(str, Enum):
    DEBUG = "Debug"
    RELEASE = "Release"


class HomelySettings(BaseModel):
    username: str
    password: str
    location: str = "Hjemme"


class MqttSettings(BaseModel):
    topic_prefix: str = "homely-mqtt"
    broker_url: str = None
    broker_port: int = 1883
    ca_certs: FilePath = None
    certfile: FilePath = None
    keyfile: FilePath = None
    publish_enabled: bool = True


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_nested_delimiter="__")

    mode: Mode = Mode.DEBUG
    bind_address: str = "127.0.0.1"
    port: int = 3000

    homely: HomelySettings = Field(default_factory=HomelySettings)
    mqtt: MqttSettings = Field(default_factory=MqttSettings)

    @property
    def debug(self):
        return self.mode == Mode.DEBUG


settings = Settings()
