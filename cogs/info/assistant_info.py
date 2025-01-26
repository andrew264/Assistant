from os import getpid
from platform import python_version

import discord
import psutil as psutil
from discord import utils
from discord.ext import commands

from assistant import AssistantBot
from config import OWNER_ID


def human_bytes(_bytes: float) -> str:
    """Converts bytes to Human Readable format"""
    for x in ["bytes", "KB", "MB", "GB", "TB", "PB"]:
        if _bytes < 1024.0:
            return f"{_bytes:.2f} {x}"
        _bytes /= 1024.0
    else:
        return "a lot"


class BotInfo(commands.Cog):
    def __init__(self, bot: AssistantBot):
        self.bot = bot

    @commands.hybrid_command(name="bot-info", aliases=["bot", "info"], description="Shows bot stats/info")
    async def assistant_info(self, ctx: commands.Context):
        user = ctx.me
        embed = discord.Embed(description=user.mention, color=discord.Color.blurple())
        embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
        embed.add_field(name="Created by", value=f"<@{OWNER_ID}>")
        embed.add_field(name="Servers", value=len(self.bot.guilds))
        embed.add_field(name="Users", value=len(self.bot.users))
        embed.add_field(name="Registered Commands", value=len(self.bot.commands))
        embed.add_field(name="Uptime", value=utils.format_dt(self.bot.start_time, style="R"))
        embed.add_field(name="Python Version", value=f"v. {python_version()}")
        used_memory = psutil.Process(getpid()).memory_info().rss
        embed.add_field(name="Python Memory Usage", value=f"{human_bytes(used_memory)}")
        embed.add_field(name=f"{discord.__title__.capitalize()} Version", value=f"v. {discord.__version__}", inline=False)
        embed.add_field(name="System CPU Usage", value=f"{psutil.cpu_percent()}%", inline=False)
        embed.add_field(name="System Memory Usage", value=f"{human_bytes(psutil.virtual_memory().used)}/" + f"{human_bytes(psutil.virtual_memory().total)}", inline=False)
        await ctx.send(embed=embed)


async def setup(bot: AssistantBot):
    await bot.add_cog(BotInfo(bot))
