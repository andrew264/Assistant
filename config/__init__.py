import tomllib
from pathlib import Path
from typing import Optional, Mapping, List

import discord

# Path to the config file
__config_file = Path(__file__).parent / "config.toml"
if not __config_file.exists():
    raise FileNotFoundError(f"Config file not found at {__config_file}")

with open(__config_file, 'rb') as f:
    config = tomllib.load(f)

# Client
DISCORD_TOKEN: Optional[str] = config["client"]["token"] or None
PREFIX: Optional[str] = config["client"]["prefix"] or None
OWNER_ID: Optional[int] = config["client"]["owner_id"] or None
LOG_LEVEL: str = config["client"]["log_level"] or "DEBUG"

# Status and activity
STATUS: discord.Status = discord.Status[config["client"]["status"]] or discord.Status.online
ACTIVITY_TYPE: discord.ActivityType = discord.ActivityType[config["client"]["activity_type"]] \
                                      or discord.ActivityType.playing
ACTIVITY_TEXT: Optional[str] = config["client"]["activity_text"] or None

# Channels
HOME_GUILD_ID: int = config["client"]["home_guild_id"] or 0
TEST_GUILDS: Optional[List[int]] = config["client"]["test_guilds"] or None
DM_RECIPIENTS_CATEGORY: int = config["client"]["dm_recipients_category"] or 0

# MongoDB
_MONGO_USERNAME: Optional[str] = config["mongo"]["username"] or None
_MONGO_PASSWORD: Optional[str] = config["mongo"]["password"] or None
_MONGO_URL: Optional[str] = config["mongo"]["url"] or None
MONGO_URI: Optional[str] = f"mongodb+srv://{_MONGO_USERNAME}:{_MONGO_PASSWORD}@{_MONGO_URL}" if _MONGO_URL else None

# Resource Path
RESOURCE_PATH: Path = Path(__file__).parent.parent / "resources"


# Reddit
class RedditConfig:
    CLIENT_ID: Optional[str] = config["reddit"]["client_id"] or None
    CLIENT_SECRET: Optional[str] = config["reddit"]["client_secret"] or None
    USERNAME: Optional[str] = config["reddit"]["username"] or None
    PASSWORD: Optional[str] = config["reddit"]["password"] or None

    def __bool__(self):
        return bool(self.CLIENT_ID and self.CLIENT_SECRET and self.USERNAME and self.PASSWORD)


LOGGING_GUILDS: Optional[Mapping[str, Mapping[str, int]]] = config["logging"] or None


# Lavalink
class LavaConfig:
    URI: Optional[str] = config["lavalink"]["uri"] or None
    PASSWORD: Optional[str] = config["lavalink"]["password"] or None

    def __bool__(self):
        return bool(self.URI and self.PASSWORD)


# YouTube
YT_API_KEY: Optional[str] = config["youtube"]["api_key"] or None

# Genius
GENIUS_TOKEN: Optional[str] = config["genius"]["token"] or None
