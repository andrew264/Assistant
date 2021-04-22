from discord import FFmpegPCMAudio
import discord.ext.commands as commands
from discord.utils import get
import os
import random

from  olmusic import listToString

class dialogues(commands.Cog):

	def __init__(self,client):
		self.client = client

	@commands.command(aliases=['d'])
	async def dialogues(self,ctx,*,arg):
		# Join VC
		voice = get(self.client.voice_clients, guild=ctx.guild)
		if voice and voice.is_connected():
			pass
		elif voice==None:
			voiceChannel = ctx.message.author.voice.channel
			voice = await voiceChannel.connect()
		if ctx.voice_client.is_playing() is True or ctx.voice_client.is_paused() is True:
			return
		# scan all dialogues
		dialogues = [os.path.splitext(filename)[0] for filename in os.listdir('./dialogues')]
		if arg == 'list':
			Names=[no_name.replace('_',' ') for no_name in dialogues]
			return await ctx.send(f'{listToString(Names)}')
		elif arg == 'random' or arg == 'rand':
			x= random.randint(0,len(dialogues))
			voice.play(FFmpegPCMAudio(f'dialogues/{dialogues[x]}.mp3'))
			name=dialogues[x].replace('_',' ')
			return await ctx.send(f'Playing: `{name}`')
		elif arg:
			name=arg.replace(' ','_')
			if name not in dialogues:
				return await ctx.send(f'`{arg}` not found.')
			voice.play(FFmpegPCMAudio(f'dialogues/{name}.mp3'))
			return await ctx.send(f'Playing: `{arg}`')

def setup(client):
	client.add_cog(dialogues(client))