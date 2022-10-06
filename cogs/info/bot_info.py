from os import getpid
from platform import python_version

import disnake
import lavalink
import psutil
from disnake.ext import commands

from EnvVariables import Owner_ID
from assistant import Client, human_bytes, relative_time, long_date


class BotInfo(commands.Cog):
    def __init__(self, client: Client):
        self.client = client

    @commands.slash_command(description="Information about the bot")
    async def bot(self, inter: disnake.ApplicationCommandInteraction) -> None:
        pass

    @bot.sub_command(name="info", description=f"Shows Bot's Info")
    async def _bot_info(self, inter: disnake.ApplicationCommandInteraction) -> None:
        user = self.client.user
        embed = disnake.Embed(color=0xFF0060, description=user.mention)
        embed.set_author(name=user, icon_url=user.avatar.url)
        embed.set_thumbnail(url=user.avatar.url)
        embed.add_field(name="Created by", value=f"<@{Owner_ID}>")
        embed.add_field(name="Created on", value=f"{long_date(user.created_at)}\n{relative_time(user.created_at)}")
        embed.add_field(name="No. of Guilds", value=f"{len(self.client.guilds)}", inline=False)
        embed.add_field(name="No. of Users", value=f"{len(self.client.users)}", inline=False)
        embed.add_field(name="Uptime", value=f"{relative_time(self.client.start_time)}", inline=False)
        embed.set_footer(text=f"User ID: {user.id}")
        await inter.response.send_message(embed=embed)

    @bot.sub_command(name="stats", description="Shows Bot's Stats")
    async def _bot_stats(self, inter: disnake.ApplicationCommandInteraction) -> None:
        user = self.client.user
        embed = disnake.Embed(color=0xFF0060, description=user.mention)
        embed.add_field(name="Python Version", value=f"v. {python_version()}")
        used_memory = psutil.Process(getpid()).memory_info().rss
        embed.add_field(name="Python Memory Usage", value=f"{human_bytes(used_memory)}")
        embed.add_field(name=f"{disnake.__title__.capitalize()} Version",
                        value=f"v. {disnake.__version__}", inline=False)
        embed.add_field(name="Lavalink Version",
                        value=f"v. {lavalink.__version__}" if lavalink is not None else "Not Installed")
        lava_stats: lavalink.Stats = self.client.lavalink.node_manager.nodes[0].stats
        embed.add_field(name="Lavalink Memory Usage",
                        value=f"{human_bytes(lava_stats.memory_used)}/{human_bytes(lava_stats.memory_allocated)}")
        embed.add_field(name="System CPU Usage", value=f"{psutil.cpu_percent()}%", inline=False)
        embed.add_field(name="System Memory Usage",
                        value=f"{human_bytes(psutil.virtual_memory().used)}/" +
                              f"{human_bytes(psutil.virtual_memory().total)}")
        embed.set_footer(text=f"User ID: {user.id}")
        await inter.response.send_message(embed=embed)


def setup(bot):
    bot.add_cog(BotInfo(bot))
