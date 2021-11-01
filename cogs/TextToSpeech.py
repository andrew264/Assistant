# Imports
from disnake import FFmpegPCMAudio, Member, Client, ApplicationCommandInteraction
from disnake.ext import commands
from disnake.ext.commands import Param
from disnake.utils import get

import os, re
from gtts import gTTS

class TextToSpeech(commands.Cog):

	def __init__(self, client: Client):
		self.client = client

	@commands.slash_command(description = "Text To Speach")
	async def tts(self,
			   inter: ApplicationCommandInteraction,
			   message : str = Param(description="Enter a message")) -> None:
		if isinstance(inter.author, Member) and inter.author.voice is None:
			return await inter.response.send_message("You are not connected to a Voice Channel.", ephemeral=True)
		voice = get(self.client.voice_clients, guild=inter.guild)
		if voice and voice.is_connected(): pass
		elif isinstance(inter.author, Member) and voice==None:
			voiceChannel = inter.author.voice.channel
			voice = await voiceChannel.connect()
		if message:
			pre_tts = os.path.isfile("tts.mp3")
			try:
				if pre_tts: os.remove("tts.mp3")
			except PermissionError: return
			name = re.sub(r'[^A-Za-z0-9 ]+', '', inter.author.display_name)
			new_str = re.sub(r'[^A-Za-z0-9 ]+', '', message)
			gTTS(f'{name} says {new_str}').save('tts.mp3')
			if voice.is_playing() == False & voice.is_playing() == False :
				voice.play(FFmpegPCMAudio('tts.mp3'))
			await inter.response.send_message(f"{inter.author.display_name} says: {message}")

def setup(client):
	client.add_cog(TextToSpeech(client))