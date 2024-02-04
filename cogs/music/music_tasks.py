import asyncio
from typing import cast, Optional

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
        if payload.player.queue or payload.player.current:
            return
        await self.bot.change_presence(status=STATUS,
                                       activity=discord.Activity(type=ACTIVITY_TYPE,
                                                                 name=ACTIVITY_TEXT), )

    @commands.Cog.listener('on_wavelink_inactive_player')
    async def _disconnect_inactive_player(self, player: wavelink.Player) -> None:
        guild = player.guild
        self.bot.logger.info(f"[LAVALINK] Disconnected from {guild}, reason: no songs in queue")
        await player.disconnect(force=True)

    def _am_i_alone(self, vc: wavelink.Player) -> bool:
        self.bot.logger.debug(f"[LAVALINK] Checking if I am alone in {vc.guild}")
        if members := vc.channel.members:
            if len(members) == 1 and members[0] == vc.guild.me:
                return True
        return False

    @commands.Cog.listener('on_voice_state_update')
    async def _disconnect_if_no_listeners(self, member: discord.Member, *args) -> None:
        guild = member.guild
        if guild.voice_client is None:
            return
        vc: wavelink.Player = cast(wavelink.Player, guild.voice_client)

        if vc.channel is None:
            return

        # at this point, we are in a voice channel
        if self._am_i_alone(vc):
            self.bot.logger.debug(
                f"[LAVALINK] Disconnecting in {SLEEP_TIME} secs from {vc.guild}, reason: no listeners")
            await asyncio.sleep(SLEEP_TIME)

            player: Optional[discord.VoiceProtocol] = discord.utils.get(self.bot.voice_clients,
                                                                        guild=guild)  # get the updated voice client
            if player is None:
                self.bot.logger.debug(
                    f"[LAVALINK] Not disconnecting from {guild}, reason: not connected")
                return
            player: wavelink.Player = cast(wavelink.Player, player)
            if self._am_i_alone(player):
                if player.playing:
                    await player.stop()
                await player.set_filters(None)
                await player.disconnect(force=True)
                self.bot.logger.debug(f"[LAVALINK] Disconnected from {guild}, reason: no listeners")

    @commands.Cog.listener('on_wavelink_track_end')
    async def _play_next_track(self, payload: wavelink.TrackEndEventPayload) -> None:
        self.bot.logger.info(f"[LAVALINK] Finished playing {payload.track.title} on {payload.player.guild}")
        if payload.player.queue or payload.player.queue.mode.loop or payload.player.queue.mode.loop_all:
            await payload.player.play(payload.player.queue.get())


async def setup(bot: AssistantBot) -> None:
    await bot.add_cog(MusicTasks(bot))
