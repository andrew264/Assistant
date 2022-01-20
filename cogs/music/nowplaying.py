import asyncio
import time

import disnake
from disnake import (
    Embed,
    Button,
    Interaction,
    ButtonStyle,
    MessageInteraction,
)
from disnake.ext import commands
from lavalink import DefaultPlayer

from cogs.music.lavaclient import VideoTrack
from cogs.music.misc import human_format


class NP(commands.Cog):
    def __init__(self, client: disnake.Client):
        self.client = client

    # Now Playing
    @commands.command(aliases=["np"])
    @commands.guild_only()
    async def nowplaying(self, ctx: commands.Context) -> None:
        player: DefaultPlayer = self.client.lavalink.player_manager.get(ctx.guild.id)
        await ctx.message.delete()

        class NowPlayingButtons(disnake.ui.View):
            def __init__(self):
                super().__init__(timeout=None)

            async def on_timeout(self):
                self.stop()

            async def interaction_check(self, interaction: MessageInteraction) -> bool:
                if interaction.author.voice is None:
                    await interaction.response.send_message("You are not connected to a voice channel.", ephemeral=True)
                    return False
                if interaction.author.voice.channel == interaction.guild.voice_client.channel:
                    return True
                await interaction.response.send_message("You must be in same VC as Bot.", ephemeral=True)
                return False

            @disnake.ui.button(emoji="⏮", style=ButtonStyle.primary)
            async def prev_button(self, button: Button, interaction: Interaction):
                await player.seek(0)
                await interaction.response.edit_message(embed=self.NPEmbed)

            @disnake.ui.button(emoji="⏪", style=ButtonStyle.primary)
            async def reverse_button(self, button: Button, interaction: Interaction):
                if player.position > 10000:
                    await player.seek(int(player.position - 10000))
                else:
                    await player.seek(0)
                await interaction.response.edit_message(embed=self.NPEmbed)

            @disnake.ui.button(emoji="⏸", style=ButtonStyle.primary)
            async def play_button(self, button: Button, interaction: Interaction):
                if player.paused is False:
                    await player.set_pause(pause=True)
                    button.emoji = "▶"
                    await interaction.response.edit_message(view=self)
                else:
                    await player.set_pause(pause=False)
                    button.emoji = "⏸"
                    await interaction.response.edit_message(view=self)

            @disnake.ui.button(emoji="⏩", style=ButtonStyle.primary)
            async def forward_button(self, button: Button, interaction: Interaction):
                if player.position < player.current.duration - 10000:
                    await player.seek(int(player.position + 10000))
                else:
                    await player.seek(int(player.current.duration))
                await interaction.response.edit_message(embed=self.NPEmbed)

            @disnake.ui.button(emoji="⏭", style=ButtonStyle.primary)
            async def skip_button(self, button: Button, interaction: Interaction):
                await player.skip()
                await interaction.response.edit_message(embed=self.NPEmbed)

            @disnake.ui.button(label="Stop", emoji="⏹", style=ButtonStyle.danger, row=1)
            async def stop_button(self, button: Button, interaction: Interaction):
                player.queue.clear()
                await player.stop()
                await interaction.guild.voice_client.disconnect(force=True)
                await interaction.response.edit_message(content="Thanks for Listening", embed=None, view=None)

            @disnake.ui.button(label="Loop", emoji="➡", style=ButtonStyle.gray, row=1)
            async def loop_button(self, button: Button, interaction: Interaction):
                if player.repeat:
                    player.set_repeat(False)
                    button.emoji = "➡"
                else:
                    player.set_repeat(True)
                    button.emoji = "🔁"
                await interaction.response.edit_message(view=self)

            @disnake.ui.button(emoji="➖", style=ButtonStyle.green, row=2)
            async def volume_down(self, button: Button, interaction: Interaction):
                if player.volume > 10:
                    await player.set_volume(player.volume - 10)
                    self.volume_up.disabled = False
                else:
                    await player.set_volume(10)
                if player.volume <= 10:
                    button.disabled = True
                self.volume.label = f"Volume: {player.volume}%"
                await interaction.response.edit_message(view=self)

            @disnake.ui.button(label="Volume", style=ButtonStyle.gray, row=2, disabled=True)
            async def volume(self, button: Button, interaction: Interaction):
                pass

            @disnake.ui.button(emoji="➕", style=ButtonStyle.green, row=2)
            async def volume_up(self, button: Button, interaction: Interaction):
                if player.volume <= 90:
                    await player.set_volume(player.volume + 10)
                    self.volume_down.disabled = False
                else:
                    await player.set_volume(100)
                    button.disabled = True
                self.volume.label = f"Volume: {player.volume}%"
                await interaction.response.edit_message(view=self)

            @property
            def NPEmbed(self) -> Embed:
                current_song: VideoTrack = player.current
                percentile = round(((player.position / 1000) / current_song.Duration) * 20)
                bar = "────────────────────"
                progress_bar = bar[:percentile] + "⚪" + bar[percentile + 1:]
                song_on = time.strftime("%M:%S", time.gmtime(player.position / 1000))
                embed = Embed(color=0xEB459E)
                embed.set_thumbnail(url=f"{current_song.Thumbnail}")
                embed.set_author(name=current_song.Title, url=current_song.uri, icon_url=current_song.avatar_url)
                embed.add_field(name=f"{song_on} {progress_bar} {current_song.FDuration}", value="\u200b",
                                inline=False, )
                embed.add_field(name="Views:", value=f"{human_format(int(current_song.Views))}", inline=True)
                embed.add_field(name="Likes:", value=f"{human_format(int(current_song.Likes))}", inline=True)
                embed.add_field(name="Uploaded on:", value=f"{current_song.UploadDate}", inline=True)
                if player.queue and player.repeat:
                    embed.set_footer(text=f"Looping through {len(player.queue) + 1} Songs")
                elif player.queue and not player.repeat:
                    embed.set_footer(text=f"Next in Queue: {player.queue[0].Title}",
                                     icon_url=player.queue[0].avatar_url)
                elif not player.queue and player.repeat:
                    embed.set_footer(text="Looping current Song")
                else:
                    embed.set_footer(text=f"Requested by {current_song.Author.display_name}")
                return embed

        if not player.is_playing:
            await ctx.send("Queue is Empty", delete_after=30)
            return
        view = NowPlayingButtons()
        msg = await ctx.send(embed=view.NPEmbed, view=view)
        while True:
            if player.is_playing and ctx.voice_client:
                pass
            else:
                try:
                    await msg.delete()
                except disnake.NotFound:
                    pass
                break
            await msg.edit(embed=view.NPEmbed)
            await asyncio.sleep(5)

    @nowplaying.before_invoke
    async def check_voice(self, ctx: commands.Context) -> None:
        player = self.client.lavalink.player_manager.get(ctx.guild.id)
        if ctx.voice_client is None or not player.is_connected:
            raise commands.CheckFailure("Bot is not connect to VC.")
        if ctx.author.voice is None:
            raise commands.CheckFailure("You are not connected to a voice channel.")
        if ctx.voice_client is not None and ctx.author.voice is not None:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                raise commands.CheckFailure("You must be in same VC as Bot.")


def setup(client):
    client.add_cog(NP(client))
