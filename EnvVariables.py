from os import getenv
from dotenv import load_dotenv
load_dotenv()
TOKEN = getenv('DISCORD_TOKEN')
DM_Channel = int(getenv('DM_CHANNEL_ID'))

# Genius API
GENIUS_TOKEN = getenv('GENIUS_API_KEY')

# Youtube Data API
YT_TOKEN = getenv('YOUTUBE_API_KEY')