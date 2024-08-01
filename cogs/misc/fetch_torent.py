import discord
from discord.ext import commands

from assistant import AssistantBot


# import libtorrent as lt


class FetchTorrent(commands.Cog):
    def __init__(self, bot: AssistantBot):
        self.bot = bot

    @staticmethod
    def fetch_torrent(magnet_link: str):
        ses = lt.session()
        info = lt.torrent_info(lt.parse_magnet_uri(magnet_link))

        return info

    @commands.hybrid_command('torrent', description="Fetches a torrent file and shows info.")
    async def torrent(self, ctx: commands.Context, url: str):
        await ctx.defer()
        info = self.fetch_torrent(url)
        embed = discord.Embed(title=info.name())
        embed.add_field(name="Size", value=info.total_size())
        embed.add_field(name="Files", value=len(info.files()))
        await ctx.send(embed=embed)
        await ctx.send(content=f'```{url}```')


async def setup(bot: AssistantBot):
    # bot.add_cog(FetchTorrent(bot))
    pass
