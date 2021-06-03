import discord.ext.commands as commands
from discord.utils import get
from gtts import gTTS
from discord import FFmpegPCMAudio
import os, re

class texttospeech(commands.Cog):

	def __init__(self,client):
		self.client = client

	@commands.command(aliases=['TTS'])
	async def tts(self, ctx, *, string:str=''):
		if ctx.author.voice is None or ctx.author.voice.channel is None:
			return await ctx.send("You are not connected to a voice channel.")
		voice = get(self.client.voice_clients, guild=ctx.guild)
		if voice and voice.is_connected():
			pass
		elif voice==None:
			voiceChannel = ctx.message.author.voice.channel
			voice = await voiceChannel.connect()
		if string:
			pre_tts = os.path.isfile("1.mp3")
			try:
				if pre_tts:
					os.remove("1.mp3")
			except PermissionError:
				await ctx.send('Hol Up')
			if ctx.message.author.nick:
				name = re.sub(r'[^A-Za-z0-9 ]+', '', ctx.message.author.nick)
			else:
				name = re.sub(r'[^A-Za-z0-9 ]+', '', ctx.message.author.name)
			if string.startswith('!'):
				lang = 'ja'
			if string.startswith('?'):
				lang = 'ta'
			else:
				lang = 'en'
			new_str = re.sub(r'[^A-Za-z0-9 ]+', '', string)
			tts = gTTS(f'{name} says {new_str}', lang=lang)
			tts.save('1.mp3')
			voice.play(FFmpegPCMAudio(f'1.mp3'))

def setup(client):
	client.add_cog(texttospeech(client))