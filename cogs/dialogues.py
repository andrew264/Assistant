import discord
import discord.ext.commands as commands
import os
import random

from  olmusic import listToString
from discord.ext.commands import has_permissions

class dialogues(commands.Cog):

	def __init__(self,client):
		self.client = client

	@commands.command(brief='This will play a Dialogue.', aliases=['d'])
	async def dialogues(self,ctx,*,arg):
		dialogues = [os.path.splitext(filename)[0] for filename in os.listdir('./dialogues')]
		if arg == 'list':
			Names=[no_name.replace('_',' ') for no_name in dialogues]
			return await ctx.send(f'{listToString(Names)}')
		if arg == 'random' or arg == 'rand':
			x= random.randint(0,len(dialogues))

			channel = ctx.message.author.voice.channel
			if ctx.voice_client:
				await ctx.voice_client.disconnect()
			voice = await channel.connect()
			source = discord.FFmpegPCMAudio(f'dialogues/{dialogues[x]}.mp3')
			player = voice.play(source)
			name=dialogues[x].replace('_',' ')
			return await ctx.send(f'Playing: `{name}`')

		if (ctx.author.voice):
			name=arg.replace(' ','_')
			if name not in dialogues:
				return await ctx.send(f'`{arg}` not found.')
			channel = ctx.message.author.voice.channel
			if ctx.voice_client:
				await ctx.voice_client.disconnect()
			voice = await channel.connect()
			source = discord.FFmpegPCMAudio(f'dialogues/{name}.mp3')
			player = voice.play(source)
			return await ctx.send(f'Playing: `{arg}`')

def setup(client):
	client.add_cog(dialogues(client))