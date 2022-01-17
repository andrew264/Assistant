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
from lavalink import DefaultPlayer

from cogs.music.loop import LoopType
from cogs.music.misc import human_format
from cogs.music.videoinfo import VideoInfo


class NowPlayingButtons(disnake.ui.View):
    def __init__(self, song_queue: list[VideoInfo], queue_prop: dict, player: DefaultPlayer):
        super().__init__(timeout=None)
        self.message: Message
        self.song_queue = song_queue
        self.queue_prop = queue_prop
        self.player = player

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
        if self.player.paused is False:
            await self.player.set_pause(pause=True)
            button.label = "Play"
            button.emoji = "▶"
            await interaction.response.edit_message(view=self)
            while self.player.paused:
                self.song_queue[0].SongIn += 1
                await asyncio.sleep(1)
        else:
            await self.player.set_pause(pause=False)
            button.label = "Pause"
            button.emoji = "⏸"
            await interaction.response.edit_message(view=self)

    @disnake.ui.button(label="Skip", emoji="⏭", style=ButtonStyle.primary)
    async def skip_button(self, button: Button, interaction: Interaction):
        await self.player.stop()
        self.song_queue[0].SongIn = 0
        await interaction.response.edit_message(embed=self.NPEmbed())

    @disnake.ui.button(label="Stop", emoji="⏹", style=ButtonStyle.danger)
    async def stop_button(self, button: Button, interaction: Interaction):
        self.song_queue[0].SongIn = 0
        self.song_queue.clear()
        await self.player.stop()
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
        if self.player.volume > 10:
            await self.player.set_volume(self.player.volume-10)
            if self.children[6].disabled:
                self.children[6].disabled = False
        else:
            await self.player.set_volume(10)
        if self.player.volume <= 10:
            button.disabled = True
        self.children[5].label = f"Volume: {self.player.volume}%"
        self.queue_prop["volume"] = self.player.volume
        await interaction.response.edit_message(view=self)

    @disnake.ui.button(label="Volume", style=ButtonStyle.gray, row=1, disabled=True)
    async def volume(self, button: Button, interaction: Interaction):
        pass

    @disnake.ui.button(emoji="➕", style=ButtonStyle.green, row=1)
    async def volume_up(self, button: Button, interaction: Interaction):
        if self.player.volume <= 90:
            await self.player.set_volume(self.player.volume+10)
            if self.children[4].disabled:
                self.children[4].disabled = False
        else:
            await self.player.set_volume(100)
            button.disabled = True
        self.children[5].label = f"Volume: {self.player.volume}%"
        self.queue_prop["volume"] = self.player.volume
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
        avatar_url = current_song.Author.display_avatar.url
        match self.queue_prop["loop"]:
            case LoopType.Disabled:
                embed.set_footer(text="Playing", icon_url=avatar_url)
            case LoopType.One:
                embed.set_footer(text="Looping current song", icon_url=avatar_url)
            case LoopType.All:
                embed.set_footer(text="Looping queue", icon_url=avatar_url)
        return embed
