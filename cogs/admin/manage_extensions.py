import discord
from discord import app_commands
from discord.ext import commands

from assistant import AssistantBot
from config import HOME_GUILD_ID


class ManageExtensions(commands.Cog):
    extensions = app_commands.Group(name="extensions",
                                    description="Manage extensions",
                                    guild_ids=[HOME_GUILD_ID],
                                    default_permissions=discord.Permissions.elevated())

    def __init__(self, bot: AssistantBot):
        self.bot = bot

    @extensions.command(name="load", description="Load an extension")
    @app_commands.describe(extension='Select an extension to load')
    async def load(self, ctx: discord.Interaction, extension: str):
        try:
            await self.bot.load_extension(f"cogs.{extension}")
        except Exception as e:
            await ctx.response.send_message(f"Failed to load extension: {extension}\n```py```", ephemeral=True)
            self.bot.logger.error(f"Failed to load extension: {extension}\n{e}")
        else:
            await ctx.response.send_message(f"Loaded extension: {extension}", ephemeral=True)
            self.bot.logger.info(f"Loaded extension: {extension}")

    @extensions.command(name="unload", description="Unload an extension")
    @app_commands.describe(extension='Select an extension to unload')
    async def unload(self, ctx: discord.Interaction, extension: str):
        try:
            await self.bot.unload_extension(extension)
        except Exception as e:
            await ctx.response.send_message(f"Failed to unload extension: {extension}\n```py```", ephemeral=True)
            self.bot.logger.error(f"Failed to unload extension: {extension}\n{e}")
        else:
            await ctx.response.send_message(f"Unloaded extension: {extension}", ephemeral=True)
            self.bot.logger.info(f"Unloaded extension: {extension}")

    @extensions.command(name="reload", description="Reload an extension")
    @app_commands.describe(extension='Select an extension to reload')
    async def reload(self, ctx: discord.Interaction, extension: str):
        try:
            await self.bot.reload_extension(extension)
        except Exception as e:
            await ctx.response.send_message(f"Failed to reload extension: {extension}\n```py```", ephemeral=True)
            self.bot.logger.error(f"Failed to reload extension: {extension}\n{e}")
        else:
            await ctx.response.send_message(f"Reloaded extension: {extension}", ephemeral=True)
            self.bot.logger.info(f"Reloaded extension: {extension}")

    @extensions.command(name="sync", description="Sync all extensions to this server")
    async def sync(self, ctx: discord.Interaction):
        synced = await self.bot.tree.sync(guild=ctx.guild)
        await ctx.response.send_message(f"Synced {len(synced)} extensions to this server", ephemeral=True)

    @extensions.command(name="desync", description="Desync all extensions")
    async def desync(self, ctx: discord.Interaction):
        self.bot.tree.clear_commands(guild=ctx.guild)
        await self.bot.tree.sync(guild=ctx.guild)
        await ctx.channel.send(content=f"Desynced all extensions from this server", delete_after=10)

    @unload.autocomplete('extension')
    @reload.autocomplete('extension')
    async def extension_autocomplete(self, ctx: discord.Interaction, extension: str):
        extensions = {ext[5:]: ext for ext in self.bot.extensions.keys() if extension.lower() in ext.lower()}
        return [app_commands.Choice(name=key, value=value) for key, value in extensions.items()][:25]


async def setup(bot: AssistantBot):
    await bot.add_cog(ManageExtensions(bot))
