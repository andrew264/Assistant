import discord
from discord.ext import commands
import os
import random

from discord.ext.commands import has_permissions

class dialogues(commands.Cog):

	def __init__(self,client):
		self.client = client

	@commands.command(brief='This will play a Dialogue.', aliases=['d'])
	async def dialogues(self,ctx,arg):
		dialogues = [os.path.splitext(filename)[0] for filename in os.listdir('./dialogues')]
		if arg == 'list':
			return await ctx.send(f'{dialogues}')
		if arg == 'random' or arg == 'rand':
			x= random.randint(0,len(dialogues))

			channel = ctx.message.author.voice.channel
			if ctx.voice_client:
				await ctx.voice_client.disconnect()
			voice = await channel.connect()
			source = discord.FFmpegPCMAudio(f'dialogues/{dialogues[x]}.mp3')
			player = voice.play(source)
			return await ctx.send(f'Playing: {dialogues[x]}')

		if (ctx.author.voice):
			channel = ctx.message.author.voice.channel
			if ctx.voice_client:
				await ctx.voice_client.disconnect()
			voice = await channel.connect()
			source = discord.FFmpegPCMAudio(f'dialogues/{arg}.mp3')
			player = voice.play(source)
			return await ctx.send(f'Playing: {arg}')

def setup(client):
	client.add_cog(dialogues(client))