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

from cogs.music.lavaclient import VideoTrack
from cogs.music.misc import human_format


class NowPlayingButtons(disnake.ui.View):
    def __init__(self, player: DefaultPlayer):
        super().__init__(timeout=None)
        self.message: Message
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
        else:
            await self.player.set_pause(pause=False)
            button.label = "Pause"
            button.emoji = "⏸"
            await interaction.response.edit_message(view=self)

    @disnake.ui.button(label="Skip", emoji="⏭", style=ButtonStyle.primary)
    async def skip_button(self, button: Button, interaction: Interaction):
        await self.player.skip()
        await interaction.response.edit_message(embed=self.NPEmbed())

    @disnake.ui.button(label="Stop", emoji="⏹", style=ButtonStyle.danger)
    async def stop_button(self, button: Button, interaction: Interaction):
        self.player.queue.clear()
        await self.player.stop()
        await interaction.guild.voice_client.disconnect(force=True)
        await interaction.response.edit_message(content="Thanks for Listening", embed=None, view=None)

    @disnake.ui.button(emoji="➡", style=ButtonStyle.gray)
    async def loop_button(self, button: Button, interaction: Interaction):
        if self.player.repeat:
            self.player.set_repeat(False)
            button.emoji = "➡"
        else:
            self.player.set_repeat(True)
            button.emoji = "🔁"
        await interaction.response.edit_message(view=self)

    @disnake.ui.button(emoji="➖", style=ButtonStyle.green, row=1)
    async def volume_down(self, button: Button, interaction: Interaction):
        if self.player.volume > 10:
            await self.player.set_volume(self.player.volume - 10)
            if self.children[6].disabled:
                self.children[6].disabled = False
        else:
            await self.player.set_volume(10)
        if self.player.volume <= 10:
            button.disabled = True
        self.children[5].label = f"Volume: {self.player.volume}%"
        await interaction.response.edit_message(view=self)

    @disnake.ui.button(label="Volume", style=ButtonStyle.gray, row=1, disabled=True)
    async def volume(self, button: Button, interaction: Interaction):
        pass

    @disnake.ui.button(emoji="➕", style=ButtonStyle.green, row=1)
    async def volume_up(self, button: Button, interaction: Interaction):
        if self.player.volume <= 90:
            await self.player.set_volume(self.player.volume + 10)
            if self.children[4].disabled:
                self.children[4].disabled = False
        else:
            await self.player.set_volume(100)
            button.disabled = True
        self.children[5].label = f"Volume: {self.player.volume}%"
        await interaction.response.edit_message(view=self)

    def NPEmbed(self) -> Embed:
        current_song: VideoTrack = self.player.current
        percentile = round(((self.player.position / 1000) / current_song.Duration) * 20)
        bar = "────────────────────"
        progress_bar = bar[:percentile] + "⚪" + bar[percentile + 1:]
        song_on = time.strftime("%M:%S", time.gmtime(self.player.position / 1000))
        embed = Embed(color=0xEB459E)
        embed.set_thumbnail(url=f"{current_song.Thumbnail}")
        embed.set_author(name=f"{current_song.Title}", url=current_song.pURL, icon_url="")
        embed.add_field(name=f"{song_on} {progress_bar} {current_song.FDuration}", value="\u200b", inline=False, )
        embed.add_field(name="Views:", value=f"{human_format(int(current_song.Views))}", inline=True)
        embed.add_field(name="Likes:", value=f"{human_format(int(current_song.Likes))}", inline=True)
        embed.add_field(name="Uploaded on:", value=f"{current_song.UploadDate}", inline=True)
        avatar_url = current_song.Author.display_avatar.url
        if self.player.queue and self.player.repeat:
            embed.set_footer(text=f"Looping through {len(self.player.queue) + 1} Songs", icon_url=avatar_url)
        elif self.player.queue and not self.player.repeat:
            embed.set_footer(text=f"Next in Queue: {self.player.queue[0].Title}", icon_url=avatar_url)
        else:
            embed.set_footer(text=f"Requested by {current_song.Author.display_name}", icon_url=avatar_url)
        return embed
