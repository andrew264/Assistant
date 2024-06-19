import discord
import wavelink
from discord.ext import commands

from assistant import AssistantBot
from config import HOME_GUILD_ID, STATUS, ACTIVITY_TYPE, ACTIVITY_TEXT
from utils import remove_brackets

SLEEP_TIME = 300


class MusicTasks(commands.Cog):
    def __init__(self, bot: AssistantBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node) -> None:
        self.bot.logger.info(f"[LAVALINK] Node {node.identifier} is ready.")

    @commands.Cog.listener('on_wavelink_track_start')
    async def _set_bot_activity(self, payload: wavelink.TrackStartEventPayload) -> None:
        if payload.player.guild.id != HOME_GUILD_ID:
            return
        track_name = remove_brackets(payload.track.title)
        await self.bot.change_presence(status=STATUS,
                                       activity=discord.Activity(type=discord.ActivityType.listening,
                                                                 name=track_name), )

    @commands.Cog.listener('on_wavelink_track_end')
    async def _reset_bot_activity(self, payload: wavelink.TrackEndEventPayload) -> None:
        if payload.player.guild.id != HOME_GUILD_ID:
            return
        if not payload.player.queue.is_empty or payload.player.current is not None:
            return
        await self.bot.change_presence(status=STATUS,
                                       activity=discord.Activity(type=ACTIVITY_TYPE,
                                                                 name=ACTIVITY_TEXT), )

    @commands.Cog.listener('on_wavelink_inactive_player')
    async def _disconnect_if_no_listeners(self, player: wavelink.Player) -> None:
        self.bot.logger.debug(f"[LAVALINK] Disconnected from {player.guild}, reason: no listeners")
        await player.disconnect(force=True)

    @commands.Cog.listener('on_wavelink_track_end')
    async def _play_next_track(self, payload: wavelink.TrackEndEventPayload) -> None:
        self.bot.logger.debug(f"[LAVALINK] Finished playing {payload.track.title} on {payload.player.guild}")
        if not payload.player.queue.is_empty or payload.player.queue.mode.loop or payload.player.queue.mode.loop_all:
            await payload.player.play(payload.player.queue.get())


async def setup(bot: AssistantBot) -> None:
    await bot.add_cog(MusicTasks(bot))
