import os
from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
OWNERID = int(os.getenv('OWNER_ID'))
GUILD = os.getenv('DISCORD_GUILD')