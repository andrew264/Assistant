import asyncio
import time

import disnake
from disnake import (
    Embed,
    Message,
    Button,
    Interaction,
    ButtonStyle,
    MessageInteraction,
)

from cogs.music.loop import LoopType
from cogs.music.misc import human_format
from cogs.music.videoinfo import VideoInfo


class NowPlayingButtons(disnake.ui.View):
    def __init__(self, song_queue, queue_prop):
        super().__init__(timeout=None)
        self.message: Message
        self.song_queue: list[VideoInfo] = song_queue
        self.queue_prop: dict = queue_prop

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

    @disnake.ui.button(label="Pause", emoji="⏸", style=ButtonStyle.primary)
    async def play_button(self, button: Button, interaction: Interaction):
        if interaction.guild.voice_client.is_playing():
            interaction.guild.voice_client.pause()
            button.label = "Play"
            button.emoji = "▶"
            await interaction.response.edit_message(view=self)
            while interaction.guild.voice_client.is_paused():
                self.song_queue[0].SongIn += 1
                await asyncio.sleep(1)
        else:
            interaction.guild.voice_client.resume()
            button.label = "Pause"
            button.emoji = "⏸"
            await interaction.response.edit_message(view=self)

    @disnake.ui.button(label="Skip", emoji="⏭", style=ButtonStyle.primary)
    async def skip_button(self, button: Button, interaction: Interaction):
        interaction.guild.voice_client.stop()
        self.song_queue[0].SongIn = 0
        await interaction.response.edit_message(embed=self.NPEmbed())

    @disnake.ui.button(label="Stop", emoji="⏹", style=ButtonStyle.danger)
    async def stop_button(self, button: Button, interaction: Interaction):
        self.song_queue[0].SongIn = 0
        self.song_queue.clear()
        await interaction.guild.voice_client.disconnect(force=True)
        await interaction.response.edit_message(content="Thanks for Listening", embed=None, view=None)

    @disnake.ui.button(emoji="➡", style=ButtonStyle.gray)
    async def loop_button(self, button: Button, interaction: Interaction):
        if self.queue_prop["loop"] == LoopType.Disabled:
            button.emoji = "🔂"
            self.queue_prop["loop"] = LoopType.One
        elif self.queue_prop["loop"] == LoopType.One:
            button.emoji = "🔁"
            self.queue_prop["loop"] = LoopType.All
        else:
            button.emoji = "➡"
            self.queue_prop["loop"] = LoopType.Disabled
        await interaction.response.edit_message(view=self)

    @disnake.ui.button(emoji="➖", style=ButtonStyle.green, row=1)
    async def volume_down(self, button: Button, interaction: Interaction):
        if interaction.guild.voice_client.source.volume > 0.10:
            interaction.guild.voice_client.source.volume -= 0.10
            if self.children[6].disabled:
                self.children[6].disabled = False
        else:
            interaction.guild.voice_client.source.volume = 0.10
        if interaction.guild.voice_client.source.volume <= 0.10:
            button.disabled = True
        self.children[5].label = f"Volume: {round(interaction.guild.voice_client.source.volume * 100)}%"
        self.queue_prop["volume"] = interaction.guild.voice_client.source.volume
        await interaction.response.edit_message(view=self)

    @disnake.ui.button(label="Volume", style=ButtonStyle.gray, row=1, disabled=True)
    async def volume(self, button: Button, interaction: Interaction):
        pass

    @disnake.ui.button(emoji="➕", style=ButtonStyle.green, row=1)
    async def volume_up(self, button: Button, interaction: Interaction):
        if interaction.guild.voice_client.source.volume <= 0.90:
            interaction.guild.voice_client.source.volume += 0.10
            if self.children[4].disabled:
                self.children[4].disabled = False
        else:
            interaction.guild.voice_client.source.volume = 1.0
            button.disabled = True
        self.children[5].label = f"Volume: {round(interaction.guild.voice_client.source.volume * 100)}%"
        self.queue_prop["volume"] = interaction.guild.voice_client.source.volume
        await interaction.response.edit_message(view=self)

    def NPEmbed(self) -> Embed:
        current_song: VideoInfo = self.song_queue[0]
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
        match self.queue_prop["loop"]:
            case LoopType.Disabled:
                embed.set_footer(text="Playing")
            case LoopType.One:
                embed.set_footer(text="Looping current song")
            case LoopType.All:
                embed.set_footer(text="Looping queue")
        return embed
