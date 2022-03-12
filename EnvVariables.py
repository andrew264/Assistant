import json
from os.path import exists

if exists("config/config.json") is False:
    raise FileNotFoundError

with open("config/config.json", "r") as configFile:
    config: dict = json.load(configFile)
    configFile.close()

TOKEN = config["DISCORD_TOKEN"]
DM_Channel = config["DM_CHANNEL_ID"]
Owner_ID = config["OWNER_ID"]

# Genius API
GENIUS_TOKEN = config["GENIUS_API_KEY"]

# Youtube Data API
YT_TOKEN = config["YOUTUBE_API_KEY"]

# Lavalink Node
LL_Host = config["LAVALINK_HOST"]
LL_Port = config["LAVALINK_PORT"]
LL_Password = config["LAVALINK_PASSWORD"]

# Guilds that are Important
HOMIES = 821758346054467584
PROB = 368297437057515522

# Log Channels
HOMIES_LOG = 891369472101863494
PROB_LOG = 880285098354835546

# Reddit things
R_CLI: str = config["REDDIT"]["R_CLIENT_ID"]
R_SEC: str = config["REDDIT"]["R_CLIENT_SECRET"]
R_USR: str = config["REDDIT"]["R_USER"]
R_PAS: str = config["REDDIT"]["R_PASS"]
