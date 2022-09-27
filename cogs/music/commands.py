# Imports
import asyncio
import typing

import disnake
import lavalink
from disnake.ext import commands
from lavalink import DefaultPlayer as Player

import assistant
from assistant import VideoTrack, time_in_seconds


class MusicCommands(commands.Cog):
    def __init__(self, client: assistant.Client):
        self.client = client
        lavalink.add_event_hook(self.track_hook)

    def cog_unload(self):
        """ Cog unload handler. This removes any event hooks that were registered. """
        self.client.lavalink._event_hooks.clear()

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

    # Group Commands
    @commands.slash_command(name="music", description="Music related commands.")
    @commands.guild_only()
    async def music(self, inter: disnake.ApplicationCommandInteraction) -> None:
        pass

    # Skip Command
    @music.sub_command(name="skip", description="Remove songs from queue, or skip the current song.")
    @commands.guild_only()
    async def skip(self, inter: disnake.ApplicationCommandInteraction,
                   index: int = commands.Param(description="Enter song index, defaults to current song",
                                               default=0)) -> None:
        player: Player = self.client.lavalink.player_manager.get(inter.guild.id)
        if not player.is_playing:
            await inter.response.send_message("Nothing is playing.", ephemeral=True)
            return
        if index == 0:
            await inter.response.send_message(
                f"{inter.author.display_name} removed `{player.current.title}` from Queue.")
            await player.skip()
        else:
            try:
                await inter.response.send_message(
                    f"{inter.author.display_name} removed `{player.queue[index - 1].title}` from Queue.")
                player.queue.pop(index - 1)
            except IndexError:
                await inter.response.send_message("Invalid index.", ephemeral=True)

    # Stop Command
    @music.sub_command(name="stop", description="Stops the current song.")
    @commands.guild_only()
    async def stop(self, inter: disnake.ApplicationCommandInteraction) -> None:
        player: Player = self.client.lavalink.player_manager.get(inter.guild.id)
        if not player.is_playing:
            await inter.response.send_message("Nothing is playing.", ephemeral=True)
            return
        if player.is_connected:
            # remove all applied filters and effects
            for _filter in list(player.filters):
                await player.remove_filter(_filter)
            # Clear the queue to ensure old tracks don't start playing
            # when someone else queues something.
            player.queue.clear()
            # Stop the current track so Lavalink consumes less resources.
            await player.stop()

        await inter.response.send_message(f"{inter.author.display_name} stopped the music.")
        if inter.guild.voice_client:
            await inter.guild.voice_client.disconnect(force=True)

    # Pause Command
    @music.sub_command(name="pause", description="Pauses the current song.")
    @commands.guild_only()
    async def pause(self, inter: disnake.ApplicationCommandInteraction) -> None:
        player: Player = self.client.lavalink.player_manager.get(inter.guild.id)
        if player.paused:
            await player.set_pause(False)
            await inter.response.send_message(
                f"{inter.author.display_name} resumed `{player.current.title}`")
        else:
            await player.set_pause(True)
            await inter.response.send_message(
                f"{inter.author.display_name} paused `{player.current.title}`")

    # Loop Command
    @music.sub_command(name="loop", description="Loops the current song.")
    async def loop(self, inter: disnake.ApplicationCommandInteraction) -> None:
        player: Player = self.client.lavalink.player_manager.get(inter.guild.id)
        player.set_repeat(repeat=not player.repeat)
        await inter.response.send_message("Loop Enabled" if player.repeat else "Loop Disabled")

    # Skip to Command
    @music.sub_command(name="skipto", description="Skips to a specific song in the queue.")
    async def skipto(self, inter: disnake.ApplicationCommandInteraction,
                     index: int =
                     commands.Param(description="Index of the song to skip to, defaults to current song",
                                    default=1)) -> None:
        player: Player = self.client.lavalink.player_manager.get(inter.guild.id)
        if index >= 1:
            try:
                await inter.response.send_message(
                    f"{inter.author.display_name} skipped to `{player.queue[index-1].title}`")
                player.queue = player.queue[index - 1:]
                await player.play()
            except IndexError:
                await inter.response.send_message("Invalid index.", ephemeral=True)

    # Seek Command
    @music.sub_command(name="seek", description="Seeks to a specific time in the current song.")
    async def seek(self, inter: disnake.ApplicationCommandInteraction,
                   time: str = commands.Param(description="Time to seek to in MM:SS format, defaults to song start",
                                              default="0")) -> None:
        player: Player = self.client.lavalink.player_manager.get(inter.guild.id)

        if player.is_playing:
            current_track: VideoTrack = VideoTrack(player.current)
            await player.seek(time_in_seconds(time) * 1000)
            await asyncio.sleep(0.5)
            await inter.response.send_message(f"{inter.author.display_name} seeked `{current_track.title}` to {time}")

    # Volume Command
    @music.sub_command(name="volume", description="Sets the volume of the player.")
    async def volume(self, inter: disnake.ApplicationCommandInteraction,
                     volume: typing.Optional[int] = commands.Param(description="Volume to set the player to. (0-100)",
                                                                   default=None, ge=0, le=100)) -> None:
        player: Player = self.client.lavalink.player_manager.get(inter.guild.id)
        volume_filter = lavalink.Volume()
        if volume is None:
            await inter.response.send_message(f"Current volume: `{player.volume}%`.")
            return
        if volume > 100 or volume < 0:
            await inter.response.send_message(f"Volume cannot be set to `{volume}%`.", ephemeral=True)
            return
        volume_filter.update(volume=volume / 100)
        await player.set_filter(volume_filter)
        await inter.response.send_message(f"***{inter.author.display_name}*** set volume to `{volume}%`.")

    @music.before_invoke
    async def ensure_voice(self, inter: disnake.ApplicationCommandInteraction) -> None:
        if not inter.author.voice or not inter.author.voice.channel:
            raise commands.CheckFailure("You are not connected to a VC.")

        player: Player = self.client.lavalink.player_manager.get(inter.guild.id)
        if player is None or not player.is_connected:
            raise commands.CheckFailure("Bot is not connected to a VC.")

        if inter.guild.me.voice and inter.guild.me.voice.channel != inter.author.voice.channel:
            raise commands.CheckFailure("You must be in same VC as Bot.")


def setup(client):
    client.add_cog(MusicCommands(client))
