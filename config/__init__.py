import os
from pathlib import Path
from typing import Optional, Mapping
import tomllib

# Path to the config file
__config_file = Path(__file__).parent / "config.toml"
if not __config_file.exists():
    raise FileNotFoundError(f"Config file not found at {__config_file}")

with open(__config_file, 'rb') as f:
    config = tomllib.load(f)

# Discord Token
bot_token: Optional[str] = config["assistant"]["token"] or None

# Other Configs
dm_receive_category: Optional[int] = config["assistant"]["dm_receive_category"] or None
error_channel: Optional[int] = config["assistant"]["error_channel"] or None
home_guild: Optional[int] = config["assistant"]["home_guild"] or None
owner_id: Optional[int] = config["assistant"]["owner_id"] or None
database_path: Optional[str] = config["assistant"]["database_path"] or None


class LavalinkConfig:
    """Lavalink Configs"""
    host: Optional[str] = config["lavalink"]["host"] or None
    port: Optional[int] = config["lavalink"]["port"] or None
    password: Optional[str] = config["lavalink"]["password"] or None
    region: Optional[str] = config["lavalink"]["region"] or None
    node_name: Optional[str] = config["lavalink"]["node_name"] or None
    JAVA_PATH: Optional[str] = config["lavalink"]["java_path"] or None
    LAVALINK_PATH: Optional[str] = config["lavalink"]["lavalink_path"] or None

    def __bool__(self) -> bool:
        return bool(self.host and self.port and self.password and self.LAVALINK_PATH)


class RedditConfig:
    """Reddit Configs"""
    client_id: Optional[str] = config["reddit"]["client_id"] or None
    client_secret: Optional[str] = config["reddit"]["client_secret"] or None
    username: Optional[str] = config["reddit"]["username"] or None
    password: Optional[str] = config["reddit"]["password"] or None

    def __bool__(self) -> bool:
        return bool(self.client_id and self.client_secret and self.username and self.password)


# Other API Keys
genius_token: Optional[str] = config["genius"]["token"] or None
yt_token: Optional[str] = config["youtube"]["token"] or None

# fun
female_roles: list[int] = config["fun"]["female_role_ids"] or []

# Clips
clips_root_dir: str = config["clips"]["root_dir"] or None
guilds_with_clips: list[int] = [int(name) for name in os.listdir(clips_root_dir) if
                                os.path.isdir(os.path.join(clips_root_dir, name))] if clips_root_dir else []

# logging
logging_guilds: Optional[Mapping[str, Mapping[str, int]]] = config["logging"] or None

# mongo
mongo_uri: Optional[str] = f'mongodb+srv://{config["mongo"]["username"]}:{config["mongo"]["password"]}@{config["mongo"]["url"]}' or None
