import asyncio
from typing import Optional

import disnake
import lavalink
from disnake.ext import commands
from lavalink import DefaultPlayer as Player

from assistant import Client, VideoTrack


class NP(commands.Cog):
    def __init__(self, client: Client):
        self.client = client

    # Now Playing
    @commands.command(aliases=["np"])
    @commands.guild_only()
    async def nowplaying(self, ctx: commands.Context) -> None:
        player: Player = self.client.lavalink.player_manager.get(ctx.guild.id)
        volume_filter = lavalink.Volume()
        vol_initial: float = (await player.get_filter('Volume')).values
        logger = self.client.logger

        await ctx.message.delete()

        class NowPlayingButtons(disnake.ui.View):
            def __init__(self):
                super().__init__(timeout=None)

            async def on_timeout(self):
                self.stop()

            async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
                if interaction.author.voice is None:
                    await interaction.response.send_message("You are not connected to a voice channel.", ephemeral=True)
                    return False
                if interaction.guild.voice_client is None:
                    await interaction.response.send_message("I am not connected to a voice channel.", ephemeral=True)
                    return False
                if interaction.author.voice.channel == interaction.guild.voice_client.channel:
                    return True
                await interaction.response.send_message("You must be in same VC as Bot.", ephemeral=True)
                return False

            @disnake.ui.button(emoji="⏮️", style=disnake.ButtonStyle.primary)
            async def prev_button(self, button: disnake.Button, interaction: disnake.Interaction):
                await player.seek(0)
                await interaction.response.edit_message(embed=self.embed)
                logger.info(f"{interaction.author} skipped to beginning of {player.current.title}")

            @disnake.ui.button(emoji="⏪", style=disnake.ButtonStyle.primary)
            async def reverse_button(self, button: disnake.Button, interaction: disnake.Interaction):
                if player.position > 10000:
                    await player.seek(int(player.position - 10000))
                else:
                    await player.seek(0)
                await interaction.response.edit_message(embed=self.embed)
                logger.info(f"{interaction.author} rewinded 10 seconds of {player.current.title}")

            @disnake.ui.button(emoji="⏸️" if player.paused else "▶️", style=disnake.ButtonStyle.primary)
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

            @disnake.ui.button(emoji="⏩", style=disnake.ButtonStyle.primary)
            async def forward_button(self, button: disnake.Button, interaction: disnake.Interaction):
                if player.position < player.current.duration - 10000:
                    await player.seek(int(player.position + 10000))
                else:
                    await player.seek(int(player.current.duration))
                await interaction.response.edit_message(embed=self.embed)
                logger.info(f"{interaction.author} fast forwarded 10 seconds of {player.current.title}")

            @disnake.ui.button(emoji="⏭️", style=disnake.ButtonStyle.primary)
            async def skip_button(self, button: disnake.Button, interaction: disnake.Interaction):
                await player.skip()
                await interaction.response.edit_message(embed=self.embed)
                logger.info(f"{interaction.author} skipped {player.current.title}")

            @disnake.ui.button(label="Stop", emoji="⏹️", style=disnake.ButtonStyle.danger, row=1)
            async def stop_button(self, button: disnake.Button, interaction: disnake.Interaction):
                # remove all applied filters and effects
                for _filter in list(player.filters):
                    await player.remove_filter(_filter)
                player.queue.clear()
                await player.stop()
                await interaction.guild.voice_client.disconnect(force=True)
                await interaction.response.edit_message(content="Thanks for Listening", embed=None, view=None)
                logger.info(f"{interaction.author} stopped the music")

            @disnake.ui.button(label="Loop", emoji="➡", style=disnake.ButtonStyle.gray, row=1)
            async def loop_button(self, button: disnake.Button, interaction: disnake.Interaction):
                player.set_repeat(repeat=not player.repeat)
                button.emoji = "🔁" if player.repeat else "➡"
                await interaction.response.edit_message(view=self)
                logger.info(f"{interaction.author} toggled loop")

            @disnake.ui.button(emoji="➖", style=disnake.ButtonStyle.green, row=2)
            async def volume_down(self, button: disnake.Button, interaction: disnake.Interaction):
                vol: float = (await player.get_filter("Volume")).values
                if vol > 0.1:
                    volume_filter.update(volume=max(round(vol - 0.1, 1), 0.1))
                    self.volume_up.disabled = False
                else:
                    volume_filter.update(volume=0.1)
                button.disabled = True if volume_filter.values <= 0.1 else False
                await player.set_filter(volume_filter)
                self.volume.label = f"Volume: {round(volume_filter.values * 100)}%"
                await interaction.response.edit_message(view=self)
                logger.info(f"{interaction.author} decreased volume by 10%")

            @disnake.ui.button(label=f"Volume: {round(vol_initial * 100)}%", style=disnake.ButtonStyle.gray,
                               row=2, disabled=True)
            async def volume(self, button: disnake.Button, interaction: disnake.Interaction):
                pass

            @disnake.ui.button(emoji="➕", style=disnake.ButtonStyle.green, row=2)
            async def volume_up(self, button: disnake.Button, interaction: disnake.Interaction):
                vol: float = (await player.get_filter("Volume")).values
                if vol <= 0.9:
                    volume_filter.update(volume=min(round(vol + 0.1, 1), 1.0))
                    self.volume_down.disabled = False
                else:
                    volume_filter.update(volume=1.0)
                button.disabled = True if volume_filter.values == 1.0 else False
                await player.set_filter(volume_filter)
                self.volume.label = f"Volume: {round(volume_filter.values * 100)}%"
                await interaction.response.edit_message(view=self)
                logger.info(f"{interaction.author} increased volume by 10%")

            async def update_buttons(self):
                # Play Button
                self.play_button.emoji = "▶️" if player.paused else "⏸️"
                self.play_button.style = disnake.ButtonStyle.success \
                    if player.paused else disnake.ButtonStyle.primary
                # Loop Button
                self.loop_button.emoji = "🔁" if player.repeat else "➡"
                # Volume Buttons
                current_volume: int = round((await player.get_filter('Volume')).values * 100)
                self.volume.label = f"Volume: {current_volume}%"
                self.volume_down.disabled = True if current_volume <= 10 else False
                self.volume_up.disabled = True if current_volume == 100 else False

            @property
            def embed(self) -> disnake.Embed:
                current_song: Optional[VideoTrack] = VideoTrack(player.current) if player.current else None
                if current_song is None:
                    return disnake.Embed(title="No Songs in Queue", description="use `/play` to add songs", )
                percentile = round((player.position / current_song.duration) * 20)
                bar = "────────────────────"
                progress_bar = bar[:percentile] + "⚪" + bar[percentile + 1:]
                song_on = current_song.format_time(player.position)
                song_end = current_song.format_time(current_song.duration)
                embed = disnake.Embed(color=0xEB459E)
                embed.set_thumbnail(url=f"{current_song.thumbnail}")
                embed.set_author(name=current_song.title, url=current_song.uri, icon_url=current_song.avatar_url)
                embed.add_field(name=f"{song_on} {progress_bar} {song_end}", value="\u200b",
                                inline=False, )
                embed.add_field(name="Views:", value=f"{current_song.views}", inline=True)
                embed.add_field(name="Likes:", value=f"{current_song.likes}", inline=True)
                embed.add_field(name="Uploaded:", value=f"{current_song.upload_date}", inline=True)
                if player.queue and player.repeat:
                    embed.set_footer(text=f"Looping through {len(player.queue) + 1} Songs")
                elif player.queue and not player.repeat:
                    embed.set_footer(text=f"Next in Queue: {player.queue[0].title}",
                                     icon_url=VideoTrack(player.queue[0]).avatar_url)
                elif not player.queue and player.repeat:
                    embed.set_footer(text="Looping current Song")
                else:
                    embed.set_footer(text=f"Requested by {current_song.requested_by}")
                return embed

        if not player.is_playing:
            await ctx.send("Queue is Empty", delete_after=30)
            return
        view = NowPlayingButtons()
        msg = await ctx.send(embed=view.embed, view=view)
        while True:
            if not player.is_playing and ctx.voice_client is None:
                try:
                    await msg.delete()
                except disnake.NotFound:
                    logger.warning("Now Playing Message was deleted before it could be deleted")
                break
            try:
                await view.update_buttons()
                await msg.edit(embed=view.embed, view=view if player.current else None)
            except disnake.NotFound:
                logger.warning("Now Playing Message was deleted before it could be edited")
            await asyncio.sleep(5)

    @nowplaying.before_invoke
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
    client.add_cog(NP(client))
