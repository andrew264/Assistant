# Imports
import disnake
from disnake.ext import commands

import assistant
from EnvVariables import TOKEN, Owner_ID, LL_Host, LL_Port, LL_Password

# Client
client = assistant.Client(
    command_prefix=('.', '+'), case_insensitive=True,
    intents=disnake.Intents.all(), help_command=None,
    owner_id=Owner_ID, description="Andrew's Assistant",
    status=disnake.Status.online,
    activity=disnake.Activity(type=disnake.ActivityType.watching, name="yall Homies."),
    lava_host=LL_Host, lava_port=LL_Port, lava_password=LL_Password,
    lava_region="in", lava_node_name="assistant-node",
    enable_debug_events=True,
)

# load all cogs
client.load_extensions("./cogs")
client.load_extensions("./cogs/admin")
client.load_extensions("./cogs/misc")
client.load_extensions("./cogs/tasks")
client.load_extensions("./cogs/info")

client.run(TOKEN)
