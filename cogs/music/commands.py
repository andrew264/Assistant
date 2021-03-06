# Imports
import asyncio

import disnake
import lavalink
from disnake.ext import commands
from lavalink import DefaultPlayer as Player

import assistant
from assistant import VideoTrack


def time_in_seconds(timestamp: str) -> int:
    """
    Converts a timestamp to seconds.
    """
    seconds = 0
    for i in timestamp.split(':'):
        if int(i) > 60 or int(i) < 0:
            i = 0
        seconds = seconds * 60 + int(i)
    return seconds


class Music(commands.Cog):
    def __init__(self, client: assistant.Client):
        self.client = client
        lavalink.add_event_hook(self.track_hook)

    def cog_unload(self):
        """ Cog unload handler. This removes any event hooks that were registered. """
        self.client.lavalink._event_hooks.clear()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: disnake.Member,
                                    before: disnake.VoiceState, after: disnake.VoiceState):
        if member != self.client.user:
            return  # We don't care about other people's voice state changes
        if before.channel and after.channel is None:
            # remove all applied filters and effects
            # Clear the queue.
            # Stop the current track.
            # Force disconnect to fix reconnecting issues.
            player: Player = self.client.lavalink.player_manager.get(member.guild.id)
            if player and player.current:
                for _filter in list(player.filters):
                    await player.remove_filter(_filter)
                player.queue.clear()
                await player.stop()
                voice = member.guild.voice_client
                await voice.disconnect(force=True)

    async def track_hook(self, event):
        # Update client's status
        # Cuz why not ?
        if isinstance(event, lavalink.events.TrackStartEvent):
            song = event.player.current
            if song:
                await self.client.change_presence(activity=disnake.Activity(type=disnake.ActivityType.listening,
                                                                            name=song.title, ))
        if isinstance(event, lavalink.events.TrackEndEvent):
            player: Player = event.player
            if not player.is_playing:
                await self.client.change_presence(status=disnake.Status.online,
                                                  activity=disnake.Activity(type=disnake.ActivityType.watching,
                                                                            name="yall Homies."), )
        if isinstance(event, lavalink.events.QueueEndEvent):
            player: Player = event.player
            await self.client.change_presence(status=disnake.Status.online,
                                              activity=disnake.Activity(type=disnake.ActivityType.watching,
                                                                        name="yall Homies."), )
            await player.stop()
            await self._dc_from_voice(player)

    async def _dc_from_voice(self, player: Player):
        """
        Disconnects the bot from a voice channel.
        """
        await asyncio.sleep(30)
        voice = self.client.get_guild(player.guild_id).voice_client
        if voice and player.is_connected and not player.is_playing:
            for _filter in list(player.filters):
                await player.remove_filter(_filter)
                await voice.disconnect(force=True)

    # Skip
    @commands.command()
    @commands.guild_only()
    async def skip(self, ctx: commands.Context, arg: int = 0) -> None:
        player: Player = self.client.lavalink.player_manager.get(ctx.guild.id)
        await ctx.message.delete()
        if not player.is_playing or arg > len(player.queue):
            return
        if 0 < arg <= len(player.queue):
            await ctx.send(f"{ctx.author.display_name} removed `{player.queue[arg - 1].title}` from Queue.",
                           delete_after=30)
            player.queue.pop(arg - 1)
        elif arg == 0:
            await ctx.send(f"{ctx.author.display_name} removed `{player.current.title}` from Queue.",
                           delete_after=30)
            await player.skip()
        self.client.logger.info(f"{ctx.author.display_name} skipped a song.")

    # Stop
    @commands.command(aliases=["dc", "kelambu"])
    @commands.guild_only()
    async def stop(self, ctx: commands.Context) -> None:
        player: Player = self.client.lavalink.player_manager.get(ctx.guild.id)
        if player.is_connected:
            # remove all applied filters and effects
            for _filter in list(player.filters):
                await player.remove_filter(_filter)
            # Clear the queue to ensure old tracks don't start playing
            # when someone else queues something.
            player.queue.clear()
            # Stop the current track so Lavalink consumes less resources.
            await player.stop()
            # Disconnect from the voice channel.
            await ctx.voice_client.disconnect(force=True)
        await ctx.message.add_reaction("👋")
        await ctx.message.delete(delay=30)
        self.client.logger.info(f"{ctx.author.display_name} stopped the music.")

    # Pause
    @commands.command()
    @commands.guild_only()
    async def pause(self, ctx: commands.Context) -> None:
        player: Player = self.client.lavalink.player_manager.get(ctx.guild.id)
        await ctx.message.delete()
        if player.paused is False:
            await player.set_pause(pause=True)
            await ctx.send(f"{ctx.author.display_name} paused `{player.current.title}`", delete_after=30)
            self.client.logger.info(f"{ctx.author.display_name} paused the music.")
        else:
            await player.set_pause(pause=False)
            await ctx.send(f"{ctx.author.display_name} resumed `{player.current.title}`", delete_after=30)
            self.client.logger.info(f"{ctx.author.display_name} resumed the music.")

    # Loop
    @commands.command(aliases=["repeat"])
    @commands.guild_only()
    async def loop(self, ctx: commands.Context) -> None:
        player: Player = self.client.lavalink.player_manager.get(ctx.guild.id)
        await ctx.message.delete()
        await player.set_repeat(repeat=not player.repeat)
        await ctx.send(content="Loop Enabled" if player.repeat else "Loop Disabled", delete_after=30)

    # Jump
    @commands.command(aliases=["skipto"])
    @commands.guild_only()
    async def jump(self, ctx: commands.Context, song_index: int = 1) -> None:
        player: Player = self.client.lavalink.player_manager.get(ctx.guild.id)
        await ctx.message.delete()
        if ctx.voice_client and player.is_playing and song_index >= 1:
            del player.queue[0:song_index - 1]
        await ctx.send("Skipped", delete_after=30)
        await player.play()
        self.client.logger.info(f"{ctx.author.display_name} skipped to a song.")

    # Seek
    @commands.command(aliases=["peek"])
    @commands.guild_only()
    async def seek(self, ctx: commands.Context, timestamp: str) -> None:
        player: Player = self.client.lavalink.player_manager.get(ctx.guild.id)
        current_track: VideoTrack = VideoTrack(player.current)

        await ctx.message.delete()
        if ctx.voice_client and player.is_playing:
            await player.seek(time_in_seconds(timestamp) * 1000)
            await asyncio.sleep(0.5)
            await ctx.send(f"Jumped to `{current_track.format_time(player.position)}`", delete_after=30)
            self.client.logger.info(f"{ctx.author.display_name} seeked to a timestamp.")

    # Volume
    @commands.command(aliases=["vol", "v"])
    @commands.guild_only()
    async def volume(self, ctx: commands.Context, volume_int: int = None) -> None:
        player: Player = self.client.lavalink.player_manager.get(ctx.guild.id)
        volume_filter = lavalink.Volume()
        current_volume: int = round((await player.get_filter('Volume')).values * 100)
        await ctx.message.delete()
        if volume_int is None:
            await ctx.send(f"Volume: {current_volume}%", delete_after=15)
        elif 0 < volume_int <= 100:
            volume_filter.update(volume=volume_int / 100)
            await player.set_filter(volume_filter)
            await ctx.send(f"Volume is set to `{round(volume_int)}%`", delete_after=15)
            self.client.logger.info(f"{ctx.author.display_name} set the volume to `{volume_int}%`.")
        else:
            await ctx.send("Set Volume between `1 and 100`.", delete_after=10)

    # Check Bot in VC
    @skip.before_invoke
    @stop.before_invoke
    @pause.before_invoke
    @loop.before_invoke
    @jump.before_invoke
    @volume.before_invoke
    async def check_voice(self, ctx: commands.Context) -> None:
        player: Player = self.client.lavalink.player_manager.get(ctx.guild.id)
        if ctx.voice_client is None or not player.is_connected:
            raise commands.CheckFailure("Bot is not connect to VC.")
        if ctx.author.voice is None:
            raise commands.CheckFailure("You are not connected to a voice channel.")
        if ctx.voice_client is not None and ctx.author.voice is not None:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                raise commands.CheckFailure("You must be in same VC as Bot.")


def setup(client):
    client.add_cog(Music(client))
