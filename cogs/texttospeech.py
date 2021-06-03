import discord.ext.commands as commands
from discord.utils import get
from gtts import gTTS
from discord import FFmpegPCMAudio
import os, re

class texttospeech(commands.Cog):

	def __init__(self,client):
		self.client = client

	@commands.command()
	async def tts(self, ctx, *, string:str=''):
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
			nick = re.sub(r'[^A-Za-z0-9 ]+', '', ctx.message.author.nick)
			tts = gTTS(f'{nick} says {string}', lang='en')
			tts.save('1.mp3')
			voice.play(FFmpegPCMAudio(f'1.mp3'))

def setup(client):
	client.add_cog(texttospeech(client))