import asyncio
import time

import disnake
from disnake import (
    Embed,
    VoiceProtocol,
    Message,
    Button,
    Interaction,
    ButtonStyle,
    MessageInteraction,
)

from cogs.music.misc import human_format
from cogs.music.videoinfo import VideoInfo


def NPEmbed(current_song: VideoInfo, voice_client: VoiceProtocol) -> Embed:
    percentile = 20 - round((current_song.SongIn / current_song.Duration) * 20)
    bar = "────────────────────"
    progress_bar = bar[:percentile] + "⚪" + bar[percentile + 1:]
    song_on = time.strftime("%M:%S", time.gmtime(current_song.Duration - current_song.SongIn))
    embed = Embed(color=0xEB459E)
    embed.set_thumbnail(url=f"{current_song.Thumbnail}")
    embed.set_author(name=f"{current_song.Title}", url=current_song.pURL, icon_url="")
    embed.add_field(name=f"{song_on} {progress_bar} {current_song.FDuration}", value="\u200b", inline=False, )
    embed.add_field(name="Views:", value=f"{human_format(int(current_song.Views))}", inline=True)
    embed.add_field(name="Likes:", value=f"{human_format(int(current_song.Likes))}", inline=True)
    embed.add_field(name="Uploaded on:", value=f"{current_song.UploadDate}", inline=True)
    if voice_client.is_playing():
        embed.set_footer(text="Playing")
    elif voice_client.is_paused():
        embed.set_footer(text="Paused")
    return embed


class NowPlayingButtons(disnake.ui.View):
    def __init__(self, song_queue):
        super().__init__(timeout=None)
        self.message: Message
        self.song_queue: list[VideoInfo] = song_queue

    async def on_timeout(self):
        try:
            self.stop()
            await self.message.delete()
        except disnake.errors.NotFound:
            pass

    async def interaction_check(self, interaction: MessageInteraction) -> bool:
        if interaction.author.voice is None:
            await interaction.response.send_message("You are not connected to a voice channel.", ephemeral=True)
            return False
        if interaction.author.voice.channel == interaction.guild.voice_client.channel:
            return True
        await interaction.response.send_message("You must be in same VC as Bot.", ephemeral=True)
        return False

    @disnake.ui.button(label="Play/Pause ⏯️", style=ButtonStyle.primary)
    async def play_button(self, button: Button, interaction: Interaction):
        if interaction.guild.voice_client.is_playing():
            interaction.guild.voice_client.pause()
            button.label = "Play ▶️"
            await interaction.response.edit_message(view=self)
            while interaction.guild.voice_client.is_paused():
                self.song_queue[0].SongIn += 1
                await asyncio.sleep(1)
        else:
            interaction.guild.voice_client.resume()
            button.label = "Pause ⏸️"
            await interaction.response.edit_message(view=self)

    @disnake.ui.button(label="Skip", emoji="⏭", style=ButtonStyle.primary)
    async def skip_button(self, button: Button, interaction: Interaction):
        interaction.guild.voice_client.stop()
        self.song_queue[0].SongIn = 0
        await interaction.response.edit_message(embed=NPEmbed(self.song_queue[0], interaction.guild.voice_client))

    @disnake.ui.button(label="Stop", emoji="⏹", style=ButtonStyle.danger)
    async def stop_button(self, button: Button, interaction: Interaction):
        self.song_queue[0].SongIn = 0
        self.song_queue.clear()
        await interaction.guild.voice_client.disconnect(force=True)
        await interaction.response.edit_message(content="Thanks for Listening", embed=None, view=None)

    @disnake.ui.button(emoji="➖", style=ButtonStyle.green, row=1)
    async def volume_down(self, button: Button, interaction: Interaction):
        if interaction.guild.voice_client.source.volume > 0.10:
            interaction.guild.voice_client.source.volume -= 0.10
            if self.children[5].disabled:
                self.children[5].disabled = False
        else:
            interaction.guild.voice_client.source.volume = 0.10
        if interaction.guild.voice_client.source.volume <= 0.10:
            button.disabled = True
        self.children[4].label = f"Volume: {round(interaction.guild.voice_client.source.volume * 100)}%"
        await interaction.response.edit_message(view=self)

    @disnake.ui.button(label="Volume", style=ButtonStyle.gray, row=1, disabled=True)
    async def volume(self, button: Button, interaction: Interaction):
        pass

    @disnake.ui.button(emoji="➕", style=ButtonStyle.green, row=1)
    async def volume_up(self, button: Button, interaction: Interaction):
        if interaction.guild.voice_client.source.volume <= 0.90:
            interaction.guild.voice_client.source.volume += 0.10
            if self.children[3].disabled:
                self.children[3].disabled = False
        else:
            interaction.guild.voice_client.source.volume = 1.0
            button.disabled = True
        self.children[4].label = f"Volume: {round(interaction.guild.voice_client.source.volume * 100)}%"
        await interaction.response.edit_message(view=self)
