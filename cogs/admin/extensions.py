import itertools

import disnake
from disnake.ext import commands

from config import home_guild
from assistant import Client


class Extensions(commands.Cog):
    def __init__(self, client: Client):
        self.bot = client
        self.logger = client.logger

    @commands.slash_command(name="extensions", description="Manage extensions.", guild_ids=[home_guild],
                            default_permission=disnake.Permissions(administrator=True))
    async def extensions(self, inter: disnake.ApplicationCommandInteraction) -> None:
        if inter.user.id != self.bot.owner_id:
            return await inter.response.send_message("You are not allowed to use this command.", ephemeral=True)

    # Load Extension
    @extensions.sub_command(name="load", description="Load an extension.")
    async def load(self, inter: disnake.ApplicationCommandInteraction,
                   extension: str = commands.Param(description="Extension to Load.")) -> None:
        try:
            self.bot.load_extension(f"cogs.{extension}")
        except Exception as e:
            await inter.response.send_message(f"{type(e).__name__}: {e}")
            self.logger.error(f"Failed to load extension: cogs.{extension}")
        else:
            await inter.response.send_message(f"Loaded extension: `cogs.{extension}`")
            self.logger.info(f"Loaded extension: cogs.{extension}")

    # Unload Extension
    @extensions.sub_command(name="unload", description="Unload an extension.")
    async def unload(self, inter: disnake.ApplicationCommandInteraction,
                     extension: str = commands.Param(description="Select an Extension to Unload.")) -> None:
        try:
            self.bot.unload_extension(extension)
        except Exception as e:
            await inter.response.send_message(f"{type(e).__name__}: {e}")
            self.logger.error(f"Failed to unload extension: {extension}")
        else:
            await inter.response.send_message(f"Unloaded extension: `{extension}`")
            self.logger.info(f"Unloaded extension: {extension}")

    # Reload Extension
    @extensions.sub_command(name="reload", description="Reload an extension.")
    async def reload(self, inter: disnake.ApplicationCommandInteraction,
                     extension: str = commands.Param(description="Select a Extension to Reload.")) -> None:
        try:
            if extension == "all":
                for extension in self.bot.extensions:
                    self.bot.reload_extension(extension)
            else:
                self.bot.reload_extension(extension)
        except Exception as e:
            await inter.response.send_message(f"{type(e).__name__}: {e}")
            self.logger.error(f"Failed to reload extension: {extension}")
        else:
            await inter.response.send_message(f"Reloaded extension: `{extension}`")
            self.logger.info(f"Reloaded extension: {extension}")

    @extensions.sub_command(name="list", description="List all extensions.")
    async def list_extensions(self, inter: disnake.ApplicationCommandInteraction) -> None:
        await inter.response.send_message(f"```{', '.join(self.bot.extensions.keys())}```")

    @unload.autocomplete('extension')
    @reload.autocomplete('extension')
    def extension_auto_complete(self, inter: disnake.ApplicationCommandInteraction,
                                extension: str) -> dict[str, str]:

        extensions = {ext[5:]: ext for ext in self.bot.extensions.keys() if extension in ext}
        return dict(itertools.islice(extensions.items(), 25))


def setup(client: Client) -> None:
    client.add_cog(Extensions(client))
