from pathlib import Path
from typing import Dict, List, Optional, Self

import yaml
from pydantic import BaseModel, Field, ValidationError


class LoggingGuildConfig(BaseModel):
    guild_id: int
    channel_id: int


class ClientConfig(BaseModel):
    token: Optional[str] = None
    prefix: Optional[str] = None
    owner_id: Optional[int] = None
    log_level: str = "DEBUG"
    status: str = "online"
    activity_type: str = "playing"
    activity_text: Optional[str] = None
    home_guild_id: int = 0
    test_guilds: Optional[List[int]] = None
    dm_recipients_category: int = 0


class MongoConfig(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    url: Optional[str] = None
    database_name: str = "assistant"

    @property
    def uri(self) -> Optional[str]:
        if self.url:
            return f"mongodb+srv://{self.username}:{self.password}@{self.url}"
        return None


class RedditConfig(BaseModel):
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None

    def __bool__(self):
        return bool(self.client_id and self.client_secret and self.username and self.password)


class LavaConfig(BaseModel):
    uri: Optional[str] = None
    password: Optional[str] = None

    def __bool__(self):
        return bool(self.uri and self.password)


class Config(BaseModel):
    client: ClientConfig = Field(default_factory=ClientConfig)
    mongo: MongoConfig = Field(default_factory=MongoConfig)
    reddit: RedditConfig = Field(default_factory=RedditConfig)
    lavalink: LavaConfig = Field(default_factory=LavaConfig)
    youtube_api_key: Optional[str] = None
    genius_token: Optional[str] = None
    tenor_api_key: Optional[str] = None
    logging_guilds: Optional[Dict[str, LoggingGuildConfig]] = None
    resource_path: str = "resources"

    @classmethod
    def load_config(cls, path: Path) -> Self:
        """Loads configuration from a YAML file."""
        if not path.exists():
            cls.dump_config(path)
            raise FileNotFoundError(f"Config file not found at {path}.\nWriting the default config.yaml to {path}")

        with path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file)

        try:
            return cls(**data)
        except ValidationError as e:
            raise ValueError(f"Invalid configuration: {e}")

    def dump_config(self, path: Path):
        """Dumps the current configuration to a YAML file."""
        with path.open("w", encoding="utf-8") as file:
            yaml.safe_dump(self.model_dump(), file, sort_keys=False, allow_unicode=True)
