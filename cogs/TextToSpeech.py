# Imports
import os
import re

import disnake
from disnake.ext import commands
from disnake.ext.commands import Param
from gtts import gTTS

import assistant


class TextToSpeech(commands.Cog):
    def __init__(self, client: assistant.Client):
        self.client = client

    @commands.slash_command(description="Text To Speech")
    @commands.guild_only()
    async def tts(self, inter: disnake.ApplicationCommandInteraction,
                  message: str = Param(description="Enter a message"), ) -> None:
        if isinstance(inter.author, disnake.Member) and inter.author.voice is None:
            await inter.response.send_message("You are not connected to a Voice Channel.", ephemeral=True)
            return
        voice = disnake.utils.get(self.client.voice_clients, guild=inter.guild)
        if voice and voice.is_connected():
            pass
        elif isinstance(inter.author, disnake.Member) and voice is None:
            voiceChannel = inter.author.voice.channel
            voice = await voiceChannel.connect()
        if message:
            pre_tts = os.path.isfile("tts.mp3")
            try:
                if pre_tts:
                    os.remove("tts.mp3")
            except PermissionError:
                return
            name = re.sub(r"[^A-Za-z0-9 ]+", "", inter.author.display_name)
            new_str = re.sub(r"[^A-Za-z0-9 ]+", "", message)
            gTTS(f"{name} says {new_str}").save("tts.mp3")
            if voice.is_playing() is False & voice.is_playing() is False:
                voice.play(disnake.FFmpegPCMAudio("tts.mp3"))
            await inter.response.send_message(f"{inter.author.display_name} says: {message}")


def setup(client):
    client.add_cog(TextToSpeech(client))
