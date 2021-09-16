import discord.ext.commands as commands
from discord.utils import get
from gtts import gTTS
from discord import FFmpegPCMAudio
import re, os
from dislash.application_commands import slash_client
from dislash.interactions.application_command import Option, OptionType
from dislash.interactions.app_command_interaction import SlashInteraction

class TextToSpeech(commands.Cog):

	def __init__(self,client):
		self.client = client

	@slash_client.slash_command(description = "Text To Speach",
							 options=[Option("message", "Enter a message", OptionType.STRING, required = True)])
	async def tts(self, inter: SlashInteraction, message:str):
		if inter.author.voice is None or inter.author.voice.channel is None:
			return await ctx.send("You are not connected to a voice channel.")
		voice = get(self.client.voice_clients, guild=inter.guild)
		if voice and voice.is_connected():
			pass
		elif voice==None:
			voiceChannel = inter.author.voice.channel
			voice = await voiceChannel.connect()
		if message:
			pre_tts = os.path.isfile("tts.mp3")
			try:
				if pre_tts:
					os.remove("tts.mp3")
			except PermissionError:
				return
			name = re.sub(r'[^A-Za-z0-9 ]+', '', inter.author.display_name)
			new_str = re.sub(r'[^A-Za-z0-9 ]+', '', message)
			gTTS(f'{name} says {new_str}').save('tts.mp3')
			voice.play(FFmpegPCMAudio('tts.mp3'))
			await inter.reply(f"{inter.author.display_name} says: {message}")

def setup(client):
	client.add_cog(TextToSpeech(client))