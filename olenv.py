import os
from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
OWNERID = int(os.getenv('OWNER_ID'))
DM_Channel = int(os.getenv('DM_CHANNEL_ID'))