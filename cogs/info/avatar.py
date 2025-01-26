import io
from typing import Union

import discord
from discord import app_commands
from discord.ext import commands

from assistant import AssistantBot


class AvatarCommands(commands.Cog):
    def __init__(self, bot: AssistantBot):
        self.bot = bot
        for command in self.build_context_menus():
            self.bot.tree.add_command(command)

    async def cog_unload(self):
        for command in self.build_context_menus():
            self.bot.tree.remove_command(command.name, type=command.type)

    def build_context_menus(self):
        return [app_commands.ContextMenu(name="View Avatar", callback=self.__view_avatar, ), ]

    @app_commands.command(name="avatar", description="Get the avatar of a user")
    @app_commands.describe(user="Select a user to get their avatar")
    async def avatar(self, ctx: discord.Interaction, user: Union[discord.User, discord.Member]):
        await ctx.response.defer()
        image_file = discord.File(fp=io.BytesIO(await user.display_avatar.read()), filename="avatar.png", description=f"{user.display_name}'s Avatar")
        await ctx.edit_original_response(content=f"# {user.display_name}'s Avatar", attachments=[image_file])

    async def __view_avatar(self, ctx: discord.Interaction, user: Union[discord.User, discord.Member]):
        embed = discord.Embed(title=f"{user.display_name}'s Avatar")
        embed.set_image(url=user.display_avatar.url)
        await ctx.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: AssistantBot):
    await bot.add_cog(AvatarCommands(bot))
