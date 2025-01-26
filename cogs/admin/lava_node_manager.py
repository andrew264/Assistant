from typing import Optional

import wavelink
from discord.ext import commands

from assistant import AssistantBot
from config import LAVA_CONFIG


class LavaNodeManager(commands.Cog):
    def __init__(self, bot: AssistantBot):
        self.bot = bot

    @commands.command(name="set-node", hidden=True)
    @commands.is_owner()
    async def update_node(self, ctx: commands.Context, uri: Optional[str] = None, password: Optional[str] = None, force: bool = False):
        if uri is None and password is None:
            if LAVA_CONFIG:
                self.bot.logger.info(f'[LAVALINK] Using {LAVA_CONFIG.URI} as URI.')
                self.bot.logger.debug(f'[LAVALINK] Connecting to {LAVA_CONFIG.URI} with password {LAVA_CONFIG.PASSWORD}')
                nodes = [wavelink.Node(uri=LAVA_CONFIG.URI, password=LAVA_CONFIG.PASSWORD, inactive_player_timeout=300, ), ]
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
