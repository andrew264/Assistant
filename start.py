# Imports
import disnake

import assistant
from config import bot_token, owner_id


# Client
def start_client() -> None:
    client = assistant.Client(
        command_prefix='.', case_insensitive=True,
        intents=disnake.Intents.all(), help_command=None,
        owner_id=owner_id, description="Andrew's Assistant",
        status=disnake.Status.online,
        activity=disnake.Activity(type=disnake.ActivityType.watching, name="yall Homies."),
        allowed_mentions=disnake.AllowedMentions.all(),
    )
    client.logger.info("Starting client...")

    # load all cogs
    client.logger.info("Loading cogs...")
    client.load_extensions("./cogs")
    client.load_extensions("./cogs/admin")
    client.load_extensions("./cogs/misc")
    client.load_extensions("./cogs/tasks")
    client.load_extensions("./cogs/info")
    client.load_extensions("./cogs/music")

    client.run(bot_token)


if __name__ == "__main__":
    start_client()
