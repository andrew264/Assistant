# Imports
import disnake

import assistant
from EnvVariables import TOKEN, Owner_ID, LL_Host, LL_Port, LL_Password


# Client
def start_client():
    client = assistant.Client(
        command_prefix=('.', '+'), case_insensitive=True,
        intents=disnake.Intents.all(), help_command=None,
        owner_id=Owner_ID, description="Andrew's Assistant",
        status=disnake.Status.online,
        activity=disnake.Activity(type=disnake.ActivityType.watching, name="yall Homies."),
        allowed_mentions=disnake.AllowedMentions.all(),
        lava_host=LL_Host, lava_port=LL_Port, lava_password=LL_Password,
        lava_region="in", lava_node_name="assistant-node",
    )
    client.logger.info("Starting client...")

    # load all cogs
    client.load_extensions("./cogs")
    client.load_extensions("./cogs/admin")
    client.load_extensions("./cogs/misc")
    client.load_extensions("./cogs/tasks")
    client.load_extensions("./cogs/info")
    client.load_extensions("./cogs/notes")

    client.logger.info("All cogs loaded.")

    client.run(TOKEN)


if __name__ == "__main__":
    start_client()
