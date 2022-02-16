# Imports
import disnake
from disnake.ext import commands
import assistant
from EnvVariables import TOKEN, Owner_ID, LL_Host, LL_Port, LL_Password

# Client
client = assistant.Client(
    command_prefix=commands.when_mentioned_or("."), case_insensitive=True,
    intents=disnake.Intents.all(), help_command=None,
    owner_id=Owner_ID, description="Andrew's Assistant",
    status=disnake.Status.online,
    activity=disnake.Activity(type=disnake.ActivityType.watching, name="yall Homies."),
    lava_host=LL_Host, lava_port=LL_Port, lava_password=LL_Password,
    lava_region="in", lava_node_name="assistant-node",
)

# load all cogs
client.load_extensions("./cogs")

client.run(TOKEN)
