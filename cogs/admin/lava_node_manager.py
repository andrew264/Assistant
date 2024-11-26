from typing import Optional

import wavelink
from discord.ext import commands

from assistant import AssistantBot
from config import LavaConfig


class LavaNodeManager(commands.Cog):
    def __init__(self, bot: AssistantBot):
        self.bot = bot

    @commands.command(name="set-node", hidden=True)
    @commands.is_owner()
    async def update_node(self, ctx: commands.Context, uri: Optional[str] = None, password: Optional[str] = None, force: bool = False):
        if uri is None and password is None:
            lconf = LavaConfig()
            if lconf:
                self.bot.logger.info(f'[LAVALINK] Using {lconf.URI} as URI.')
                self.bot.logger.debug(f'[LAVALINK] Connecting to {lconf.URI} with password {lconf.PASSWORD}')
                nodes = [wavelink.Node(uri=lconf.URI, password=lconf.PASSWORD, inactive_player_timeout=300, ), ]
            else:
                return await ctx.reply('No default Lavalink config')
        else:
            self.bot.logger.info(f'[LAVALINK] Using {uri} as URI.')
            self.bot.logger.debug(f'[LAVALINK] Connecting to {uri} with password {password}')
            nodes = [wavelink.Node(uri=uri, password=password, inactive_player_timeout=300, ), ]
        await ctx.message.delete()
        if force:
            self.bot.logger.info(f'[LAVALINK] Force disconnecting from all previous nodes')
            await wavelink.Pool.close()
        await wavelink.Pool.connect(nodes=nodes, client=self.bot, cache_capacity=None)
        await ctx.channel.send('Node Updated Successfully', delete_after=10)


async def setup(bot: AssistantBot):
    await bot.add_cog(LavaNodeManager(bot))
