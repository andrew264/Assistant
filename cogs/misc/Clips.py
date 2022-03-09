import os
from typing import Optional

import disnake
from disnake.ext import commands

from assistant import Client


class Clips(commands.Cog):
    def __init__(self, client: Client):
        self.client = client

    class SelectClip(disnake.ui.Select):
        def __init__(self):
            options = [disnake.SelectOption(label=clip) for clip in os.listdir("clips/") if clip.endswith(".mp3")]
            super().__init__(
                placeholder="Select a clip",
                custom_id="clips",
                min_values=1,
                max_values=1,
                options=options, )

        async def callback(self, interaction: disnake.MessageInteraction):
            await interaction.response.edit_message(content=f"Selected: {self.values[0]}")

    class Buttons(disnake.ui.View):
        def __init__(self, voice):
            super().__init__(timeout=60)
            self.select = Clips.SelectClip()
            self.add_item(self.select)
            self.voice: disnake.VoiceClient = voice

        @disnake.ui.button(emoji="▶️", style=disnake.ButtonStyle.primary)
        async def play(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
            if self.select.values:
                clip = f"clips/{self.select.values[0]}"
            else:
                await interaction.response.edit_message(content="No clip selected", view=self)
                return
            if self.voice.is_playing:
                self.voice.stop()
            self.voice.play(disnake.FFmpegPCMAudio(clip))
            await interaction.response.edit_message(content=f"Playing {self.select.values[0]}...")

        @disnake.ui.button(emoji="⏹️", style=disnake.ButtonStyle.danger)
        async def stop(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
            if self.voice:
                await self.voice.disconnect(force=True)
            await interaction.response.edit_message(content="Bye have a great time", view=None)

    @commands.slash_command(name="clips")
    @commands.guild_only()
    async def clips(self, inter: disnake.ApplicationCommandInteraction) -> None:
        """Play mp3 in Voice Channel """
        voice: Optional[disnake.VoiceClient] = disnake.utils.get(self.client.voice_clients, guild=inter.guild)
        if voice is None:
            voice_channel = inter.author.voice.channel
            voice: disnake.VoiceClient = await voice_channel.connect()
        await inter.response.send_message("Select a clip", view=Clips.Buttons(voice))

    # Checks
    @clips.before_invoke
    async def check_clip(self, inter: disnake.ApplicationCommandInteraction) -> None:
        if inter.author.voice is None:
            raise commands.CheckFailure("You are not connected to a voice channel.")
        if inter.guild.voice_client is not None and inter.author.voice is not None:
            if inter.guild.voice_client.channel != inter.author.voice.channel:
                raise commands.CheckFailure("You must be in same VC as Bot.")
        permissions = inter.author.voice.channel.permissions_for(inter.me)
        if not permissions.connect or not permissions.speak:
            raise commands.CheckFailure('Missing `CONNECT` and `SPEAK` permissions.')


def setup(client: Client):
    client.add_cog(Clips(client))
