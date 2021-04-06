import discord
from discord.ext import commands
from olenv import *

class ready(commands.Cog):

	def __init__(self,client):
		self.client = client

	# Start
	@commands.Cog.listener()
	async def on_ready(self):
		await self.client.change_presence(status=discord.Status.idle, activity=discord.Activity(type=discord.ActivityType.watching, name="my Homies."))
		for guild in self.client.guilds:
			if guild.name == GUILD:
				break
		print(
			f'{self.client.user} is connected to the following guild:\n'
			f'\t{guild.name}(id: {guild.id})'
		)

	# Unknown commands
	@commands.Cog.listener()
	async def on_command_error(self, ctx, error):
		if isinstance(error, commands.CommandNotFound):
			await ctx.send('Unknown command used.')

def setup(client):
	client.add_cog(ready(client))