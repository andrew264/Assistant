import os
from pathlib import Path

import discord

from models.config_models import Config

# Path to the config file
if 'CONFIG_PATH' in os.environ:
    CONFIG_PATH = Path(os.environ.get('CONFIG_PATH'))
else:
    CONFIG_PATH = Path(__file__).parent / "config.yaml"

print(f"Config: {CONFIG_PATH}")
config = Config.load_config(CONFIG_PATH)

# Client
DISCORD_TOKEN = config.client.token
PREFIX = config.client.prefix
OWNER_ID = config.client.owner_id
LOG_LEVEL = config.client.log_level

# Status and activity
STATUS = discord.Status[config.client.status]
ACTIVITY_TYPE = discord.ActivityType[config.client.activity_type]
ACTIVITY_TEXT = config.client.activity_text

# Channels
HOME_GUILD_ID = config.client.home_guild_id
TEST_GUILDS = config.client.test_guilds
DM_RECIPIENTS_CATEGORY = config.client.dm_recipients_category

# MongoDB
MONGO_URI = config.mongo.uri
DATABASE_NAME = config.mongo.database_name

# Resource Path
RESOURCE_PATH = Path(config.resource_path)

# Logging
LOGGING_GUILDS = config.logging_guilds

# Lavalink
LAVA_CONFIG = config.lavalink

# Reddit
REDDIT_CONFIG = config.reddit

# YouTube
YT_API_KEY = config.youtube_api_key

# Genius
GENIUS_TOKEN = config.genius_token

# YouTube
TENOR_API_KEY = config.tenor_api_key
