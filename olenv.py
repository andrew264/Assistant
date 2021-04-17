from os import getenv
from dotenv import load_dotenv
load_dotenv()
TOKEN = getenv('DISCORD_TOKEN')
OWNERID = int(getenv('OWNER_ID'))
GUILD = getenv('DISCORD_GUILD')