import discord
from discord import app_commands
from discord.ext import commands

from assistant import AssistantBot
from config import HOME_GUILD_ID
from utils import owner_only


class UpdateAvatar(commands.Cog):
    def __init__(self, bot: AssistantBot):
        self.bot = bot

    @app_commands.command(name="change_avatar", description="Update the bot's avatar", )
    @app_commands.guilds(HOME_GUILD_ID)
    @app_commands.describe(image='Select an image to update the bot\'s avatar')
    @app_commands.check(owner_only)
    async def change_avatar(self, ctx: discord.Interaction, image: discord.Attachment):
        await ctx.response.defer(thinking=True)
        try:
            assert self.bot.user
            await self.bot.user.edit(avatar=await image.read())
            await ctx.edit_original_response(content="Updated avatar", attachments=[await image.to_file()])
            self.bot.logger.info("Updated avatar")
        except Exception as e:
            await ctx.edit_original_response(content=f"Failed to update avatar\n```py\n{e}```")
            self.bot.logger.error(f"Failed to update avatar\n{e}")


async def setup(bot: AssistantBot):
    await bot.add_cog(UpdateAvatar(bot))
