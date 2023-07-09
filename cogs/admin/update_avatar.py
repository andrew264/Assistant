import discord
from discord import app_commands
from discord.ext import commands

from assistant import AssistantBot
from config import HOME_GUILD_ID


class UpdateAvatar(commands.Cog):
    def __init__(self, bot: AssistantBot):
        self.bot = bot

    @app_commands.command(name="change-avatar", description="Update the bot's avatar", )
    @app_commands.guilds(HOME_GUILD_ID)
    @app_commands.describe(image='Select an image to update the bot\'s avatar')
    @commands.is_owner()
    async def change_avatar(self, ctx: discord.Interaction, image: discord.Attachment):
        await ctx.response.defer()
        try:
            assert self.bot.user
            await self.bot.user.edit(avatar=await image.read())
        except Exception as e:
            await ctx.edit_original_response(content="Failed to update avatar\n```py\n{e}```")
            self.bot.logger.error(f"Failed to update avatar\n{e}")
        else:
            await ctx.edit_original_response(content="Updated avatar", attachments=[image])
            self.bot.logger.info("Updated avatar")


async def setup(bot: AssistantBot):
    await bot.add_cog(UpdateAvatar(bot))
