from os.path import exists
import json

if exists("config/config.json") is False:
    raise FileNotFoundError

with open("config/config.json", "r") as configFile:
    config: dict = json.load(configFile)
    configFile.close()

TOKEN = config["DISCORD_TOKEN"]
DM_Channel = config["DM_CHANNEL_ID"]

# Genius API
GENIUS_TOKEN = config["GENIUS_API_KEY"]

# Youtube Data API
YT_TOKEN = config["YOUTUBE_API_KEY"]
