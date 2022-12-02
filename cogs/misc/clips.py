import os
from typing import Optional

import disnake
from disnake.ext import commands
from fuzzywuzzy import process

from assistant import Client


class Clips(commands.Cog):
    def __init__(self, client: Client):
        self.client = client

    @commands.slash_command(name="clips", description="Play Audio Clips in VC",
                            guild_ids=[int(name) for name in os.listdir("./clips") if
                                       os.path.isdir(os.path.join("./clips", name))])
    @commands.guild_only()
    async def clips(self, inter: disnake.ApplicationCommandInteraction,
                    clip: str = commands.Param(description="Select a Voice Clip.", default=None)) -> None:
        await inter.response.defer()
        """Play mp3 in Voice Channel """
        voice: Optional[disnake.VoiceClient] = disnake.utils.get(self.client.voice_clients, guild=inter.guild)

        class ClipView(disnake.ui.View):
            def __init__(self):
                super().__init__(timeout=60)

                class ClipDropdown(disnake.ui.Select):
                    def __init__(self):
                        super().__init__(placeholder="Select a clip", custom_id="clips", min_values=1, max_values=1,
                                         options=[disnake.SelectOption(label=c)
                                                  for c in os.listdir(f'clips/{inter.guild.id}') if
                                                  c.endswith('.mp3')], )

                    async def callback(self, interaction: disnake.MessageInteraction):
                        await interaction.response.edit_message(content=f"Playing {self.values[0]}...")
                        if voice.is_playing:
                            voice.stop()
                        voice.play(disnake.FFmpegPCMAudio(f"clips/{inter.guild.id}/{self.values[0]}"))

                self.add_item(ClipDropdown())

            async def on_timeout(self) -> None:
                if voice:
                    await voice.disconnect(force=True)
                try:
                    await inter.delete_original_message(delay=2)
                except disnake.HTTPException:
                    pass

            @disnake.ui.button(emoji="🔄", style=disnake.ButtonStyle.primary)
            async def repeat_button(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
                if interaction.guild.voice_client is None:
                    await interaction.response.edit_message(
                        content="Disconnected for Voice. Use `/clip` to play clips.", view=None)
                    self.stop()
                    return
                for child in self.children:
                    if isinstance(child, disnake.ui.Select):
                        if child.values:
                            c = child.values[0]
                            break
                else:
                    await interaction.response.edit_message(content="No clip selected", view=self)
                    return
                if voice and voice.is_playing:
                    voice.stop()
                voice.play(disnake.FFmpegPCMAudio(f"clips/{inter.guild.id}/{c}"))
                await interaction.response.edit_message(content=f"Playing {c}...")

            @disnake.ui.button(emoji="⏹️", style=disnake.ButtonStyle.danger)
            async def stop_button(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
                await voice.disconnect(force=True)
                await interaction.response.edit_message(content="Bye have a great time", view=None)
                await interaction.delete_original_message(delay=30)

        if voice is None:
            voice_channel: disnake.VoiceChannel = inter.author.voice.channel
            voice: disnake.VoiceClient = await voice_channel.connect()

        if clip and os.path.exists(f"clips/{inter.guild.id}/{clip}.mp3"):
            await inter.edit_original_message(f"Playing {clip}...", view=ClipView())
            if voice.is_playing:
                voice.stop()
            voice.play(disnake.FFmpegPCMAudio(f"clips/{inter.guild.id}/{clip}.mp3"))
        else:
            await inter.edit_original_message("Select a clip", view=ClipView())

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

    @clips.autocomplete('clip')
    async def clip_autocomplete(self, inter: disnake.ApplicationCommandInteraction, clip: str) -> list[str]:
        all_clips = [c.rstrip('.mp3') for c in os.listdir(f'clips/{inter.guild.id}') if c.endswith('.mp3')]
        return [m[0] for m in process.extract(clip, all_clips, limit=5)]


def setup(client: Client):
    client.add_cog(Clips(client))
