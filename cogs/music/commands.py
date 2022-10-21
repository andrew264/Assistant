# Imports
import asyncio
import math
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
        self.logger = client.logger
        self.player_manager = client.lavalink.player_manager
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
        if before.channel and not after.channel:
            # remove all applied filters and effects
            # Clear the queue.
            # Stop the current track.
            # Force disconnect to fix reconnecting issues.
            player: Player = self.player_manager.get(member.guild.id)
            if player and player.current:
                for _filter in list(player.filters):
                    await player.remove_filter(_filter)
                player.queue.clear()
                await player.stop()
                voice = member.guild.voice_client
                if voice:
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
        player: Player = self.player_manager.get(inter.guild.id)
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
        player: Player = self.player_manager.get(inter.guild.id)
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
        player: Player = self.player_manager.get(inter.guild.id)
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
        player: Player = self.player_manager.get(inter.guild.id)
        player.set_repeat(repeat=not player.repeat)
        await inter.response.send_message("Loop Enabled" if player.repeat else "Loop Disabled")

    # Skip to Command
    @music.sub_command(name="skipto", description="Skips to a specific song in the queue.")
    async def skip_to(self, inter: disnake.ApplicationCommandInteraction,
                      index: int =
                      commands.Param(description="Index of the song to skip to, defaults to current song",
                                     default=1)) -> None:
        player: Player = self.player_manager.get(inter.guild.id)
        if index >= 1:
            try:
                await inter.response.send_message(
                    f"{inter.author.display_name} skipped to `{player.queue[index - 1].title}`")
                player.queue = player.queue[index - 1:]
                await player.play()
            except IndexError:
                await inter.response.send_message("Invalid index.", ephemeral=True)

    # Seek Command
    @music.sub_command(name="seek", description="Seeks to a specific time in the current song.")
    async def seek(self, inter: disnake.ApplicationCommandInteraction,
                   time: str = commands.Param(description="Time to seek to in MM:SS format, defaults to song start",
                                              default="0")) -> None:
        player: Player = self.player_manager.get(inter.guild.id)

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
        player: Player = self.player_manager.get(inter.guild.id)
        if volume is None:
            await inter.response.send_message(f"Current volume: `{player.volume}%`.")
            return
        if volume > 100 or volume < 0:
            await inter.response.send_message(f"Volume cannot be set to `{volume}%`.", ephemeral=True)
            return
        volume_filter = lavalink.Volume()
        volume_filter.update(volume=volume / 100)
        await player.set_filter(volume_filter)
        await inter.response.send_message(f"***{inter.author.display_name}*** set volume to `{volume}%`.")

    # Now Playing Command
    @music.sub_command(name="nowplaying", description="Shows the current song.")
    async def nowplaying(self, inter: disnake.ApplicationCommandInteraction) -> None:
        await inter.response.defer()
        player: Player = self.player_manager.get(inter.guild.id)
        if not player.is_playing:
            await inter.response.edit_message("Nothing is playing.")
            return
        logger = self.client.logger
        volume_filter = lavalink.Volume()

        class NowPlayingView(disnake.ui.View):
            def __init__(self):
                super().__init__(timeout=None)

            @property
            def embed(self) -> disnake.Embed:

                current_track: typing.Optional[VideoTrack] = VideoTrack(player.current) if player.current else None
                if not current_track:
                    return disnake.Embed(title="No Songs in Queue", description="use `/play` to add songs", )
                _embed = disnake.Embed(colour=0x1ED760)
                _embed.set_author(name=current_track.title, url=current_track.uri, icon_url=current_track.avatar_url)
                _embed.set_thumbnail(url=current_track.thumbnail)
                bar = "────────────────────"
                percentile = round((player.position / current_track.duration) * len(bar))
                progress_bar = bar[:percentile] + "⚪" + bar[percentile + 1:]
                song_on = current_track.format_time(player.position)
                song_end = current_track.format_time(current_track.duration)
                _embed.add_field(name=f"{song_on} {progress_bar} {song_end}", value="\u200b", inline=False, )
                _embed.add_field(name="Views:", value=f"{current_track.views}", inline=True)
                _embed.add_field(name="Likes:", value=f"{current_track.likes}", inline=True)
                _embed.add_field(name="Uploaded:", value=f"{current_track.upload_date}", inline=True)
                if player.queue and player.repeat:
                    _embed.set_footer(text=f"Looping through {len(player.queue) + 1} Songs")
                elif player.queue and not player.repeat:
                    _embed.set_footer(text=f"Next in Queue: {player.queue[0].title}",
                                      icon_url=VideoTrack(player.queue[0]).avatar_url)
                elif not player.queue and player.repeat:
                    _embed.set_footer(text="Looping current Song")
                else:
                    _embed.set_footer(text=f"Requested by {current_track.requested_by}")

                return _embed

            async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
                if (not interaction.author.voice or not interaction.guild.voice_client or
                        interaction.author.voice.channel != interaction.guild.voice_client.channel):
                    await interaction.response.send_message(
                        "You must be in the same VC as the bot to use this.",
                        ephemeral=True)
                    return False
                return True

            # Previous Button
            @disnake.ui.button(emoji="⏮️", style=disnake.ButtonStyle.primary,
                               custom_id="assistant:nowplaying:prev_button")
            async def prev_button(self, button: disnake.Button, interaction: disnake.Interaction):
                await player.seek(0)
                await interaction.response.edit_message(embed=self.embed)
                logger.info(f"{interaction.author} skipped to beginning of {player.current.title}")

            # Rewind Button
            @disnake.ui.button(emoji="⏪", style=disnake.ButtonStyle.primary,
                               custom_id="assistant:nowplaying:rewind_button")
            async def rewind_button(self, button: disnake.Button, interaction: disnake.Interaction):
                if player.position > 10000:
                    await player.seek(int(player.position - 10000))
                else:
                    await player.seek(0)
                await interaction.response.edit_message(embed=self.embed)
                logger.info(f"{interaction.author} rewound 10 seconds in {player.current.title}")

            # Play/Pause Button
            @disnake.ui.button(emoji="⏸️",
                               style=disnake.ButtonStyle.primary,
                               custom_id="assistant:nowplaying:pause_button")
            async def play_button(self, button: disnake.Button, interaction: disnake.Interaction):
                if player.paused is False:
                    await player.set_pause(pause=True)
                    button.emoji = "▶️"
                    button.style = disnake.ButtonStyle.success
                    logger.info(f"{interaction.author} paused {player.current.title}")
                else:
                    await player.set_pause(pause=False)
                    button.emoji = "⏸️"
                    button.style = disnake.ButtonStyle.primary
                    logger.info(f"{interaction.author} resumed {player.current.title}")
                await interaction.response.edit_message(view=self)

            # Fast Forward Button
            @disnake.ui.button(emoji="⏩", style=disnake.ButtonStyle.primary,
                               custom_id="assistant:nowplaying:forward_button")
            async def forward_button(self, button: disnake.Button, interaction: disnake.Interaction):
                if player.position < player.current.duration - 10000:
                    await player.seek(int(player.position + 10000))
                else:
                    await player.seek(int(player.current.duration))
                await interaction.response.edit_message(embed=self.embed)
                logger.info(f"{interaction.author} fast forwarded 10 seconds of {player.current.title}")

            # Skip Button
            @disnake.ui.button(emoji="⏭️", style=disnake.ButtonStyle.primary,
                               custom_id="assistant:nowplaying:skip_button")
            async def skip_button(self, button: disnake.Button, interaction: disnake.Interaction):
                await player.skip()
                await interaction.response.edit_message(embed=self.embed)
                logger.info(f"{interaction.author} skipped {player.current.title}")

            # Stop Button
            @disnake.ui.button(label="Stop", emoji="⏹️", style=disnake.ButtonStyle.danger, row=1,
                               custom_id="assistant:nowplaying:stop_button")
            async def stop_button(self, button: disnake.Button, interaction: disnake.Interaction):
                # remove all applied filters and effects
                for _filter in list(player.filters):
                    await player.remove_filter(_filter)
                player.queue.clear()
                await player.stop()
                await interaction.guild.voice_client.disconnect(force=True)
                await interaction.response.edit_message(content="Thanks for Listening", embed=None, view=None)
                logger.info(f"{interaction.author} stopped the music")

            # Repeat Button
            @disnake.ui.button(label="Loop", emoji="🔁", style=disnake.ButtonStyle.gray, row=1,
                               custom_id="assistant:nowplaying:loop_button")
            async def loop_button(self, button: disnake.Button, interaction: disnake.Interaction):
                player.set_repeat(repeat=not player.repeat)
                button.emoji = "🔁" if player.repeat else "➡"
                await interaction.response.edit_message(view=self)
                logger.info(f"{interaction.author} toggled loop")

            # Volume-down Button
            @disnake.ui.button(emoji="➖", style=disnake.ButtonStyle.green, row=2,
                               custom_id="assistant:nowplaying:volume_down_button")
            async def volume_down(self, button: disnake.Button, interaction: disnake.Interaction):
                vol: float = (player.get_filter("Volume")).values
                if vol > 0.1:
                    volume_filter.update(volume=max(round(vol - 0.1, 1), 0.1))
                    self.volume_up.disabled = False
                else:
                    volume_filter.update(volume=0.1)
                button.disabled = True if volume_filter.values <= 0.1 else False
                await player.set_filter(volume_filter)
                self.volume.label = f"Volume: {round(volume_filter.values * 100)}%"
                await interaction.response.edit_message(view=self)
                logger.info(f"{interaction.author} set volume to {round(volume_filter.values * 100)}%")

            # Volume Button
            @disnake.ui.button(label=f"Volume: {round(player.get_filter('Volume').values)}%",
                               style=disnake.ButtonStyle.gray, row=2, disabled=True)
            async def volume(self, button: disnake.Button, interaction: disnake.Interaction):
                pass

            # Volume-up Button
            @disnake.ui.button(emoji="➕", style=disnake.ButtonStyle.green, row=2,
                               custom_id="assistant:nowplaying:volume_up_button")
            async def volume_up(self, button: disnake.Button, interaction: disnake.Interaction):
                vol: float = (player.get_filter("Volume")).values
                if vol <= 0.9:
                    volume_filter.update(volume=min(round(vol + 0.1, 1), 1.0))
                    self.volume_down.disabled = False
                else:
                    volume_filter.update(volume=1.0)
                button.disabled = True if volume_filter.values == 1.0 else False
                await player.set_filter(volume_filter)
                self.volume.label = f"Volume: {round(volume_filter.values * 100)}%"
                await interaction.response.edit_message(view=self)
                logger.info(f"{interaction.author} set volume to {round(volume_filter.values * 100)}%")

            def update_buttons(self):
                if not player.current and not player.queue:
                    for button in self.children:
                        button.disabled = True
                    self.stop()
                    return
                # Play Button
                self.play_button.emoji = "▶️" if player.paused else "⏸️"
                self.play_button.style = disnake.ButtonStyle.success \
                    if player.paused else disnake.ButtonStyle.primary
                # Loop Button
                self.loop_button.emoji = "🔁" if player.repeat else "➡"
                # Volume Buttons
                current_volume: int = round((player.get_filter('Volume')).values * 100)
                self.volume.label = f"Volume: {current_volume}%"
                self.volume_down.disabled = True if current_volume <= 10 else False
                self.volume_up.disabled = True if current_volume == 100 else False

        view = NowPlayingView()

        while True:
            view.update_buttons()
            try:
                await inter.edit_original_message(embed=view.embed, view=view)
            except disnake.HTTPException:
                break
            while player.paused:
                await asyncio.sleep(1)
            if not player.is_playing or not inter.guild.me.voice:
                break
            await asyncio.sleep(5)

    # Queue command
    @music.sub_command(name="queue", description="View the songs in Queue")
    async def queue(self, inter: disnake.ApplicationCommandInteraction):
        player: Player = self.player_manager.get(inter.guild.id)

        class QueuePages(disnake.ui.View):
            def __init__(self):
                super(QueuePages, self).__init__(timeout=180)
                self.page_no = 1

            async def on_timeout(self) -> None:
                self.stop()

            @disnake.ui.button(emoji="◀", style=disnake.ButtonStyle.secondary)
            async def prev_page(self, button: disnake.Button, interaction: disnake.Interaction):
                if self.page_no > 1:
                    self.page_no -= 1
                else:
                    self.page_no = math.ceil(len(player.queue) / 4)
                await interaction.response.edit_message(embed=self.embed, view=self)

            @disnake.ui.button(emoji="▶", style=disnake.ButtonStyle.secondary)
            async def next_page(self, button: disnake.Button, interaction: disnake.Interaction):
                if self.page_no < math.ceil(len(player.queue) / 4):
                    self.page_no += 1
                else:
                    self.page_no = 1
                await interaction.response.edit_message(embed=self.embed, view=self)

            @property
            def embed(self) -> disnake.Embed:
                first = (self.page_no * 4) - 4
                if (self.page_no * 4) + 1 <= len(player.queue):
                    last = (self.page_no * 4)
                else:
                    last = len(player.queue)
                song_index = [i for i in range(first, last)]
                if not player.current:
                    return disnake.Embed(title="Queue is Empty", colour=0xFFA31A)
                embed = disnake.Embed(
                    title="Now Playing", colour=0xFFA31A,
                    description=f"{str(player.current)}", )
                if len(player.queue) >= 1:
                    next_songs = "\u200b"
                    max_page = math.ceil(len(player.queue) / 4)
                    for i in song_index:
                        next_songs += f"{i + 1}. {str(player.queue[i])}\n"
                    embed.add_field(name=f"Next Up ({self.page_no}/{max_page})", value=next_songs, inline=False)
                if player.repeat:
                    embed.set_footer(text=f"Looping through {len(player.queue) + 1} Songs")
                else:
                    embed.set_footer(text=f"{len(player.queue) + 1} Songs in Queue")
                return embed

        view = QueuePages()
        await inter.response.send_message(embed=view.embed, view=view)

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
