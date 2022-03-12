# Imports
import asyncio
import io
import re
from typing import Optional

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
        if inter.author.voice is None:
            await inter.response.send_message("You are not connected to a Voice Channel.", ephemeral=True)
            return
        voice: Optional[disnake.VoiceClient] = disnake.utils.get(self.client.voice_clients, guild=inter.guild)
        if voice is None:
            vc = inter.author.voice.channel
            voice = await vc.connect()
        if inter.author.voice.channel != voice.channel:
            await inter.response.send_message("You are not connected to the same Voice Channel.", ephemeral=True)
            return
        if message:
            await inter.response.send_message(f"{inter.author.display_name} says: {message}")
            # Clean up the message
            clean_name = re.sub(r"[^A-Za-z0-9 ]+", "", inter.author.display_name)
            clean_msg = re.sub(r"[^A-Za-z0-9 ]+", "", message)
            # Create audio object
            audio = io.BytesIO()
            gTTS(f"{clean_name} says {clean_msg}").write_to_fp(audio)
            with audio:
                audio.seek(0)
                source = disnake.FFmpegPCMAudio(audio, pipe=True)
                # Play audio
                if voice.is_playing:
                    voice.stop()
                voice.play(source)
            # audio.close()


def setup(client):
    client.add_cog(TextToSpeech(client))
