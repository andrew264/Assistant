import discord
from discord.ext import commands

class ready(commands.Cog):

	def __init__(self,client):
		self.client = client

	# Start
	@commands.Cog.listener()
	async def on_ready(self):
		await self.client.change_presence(status=discord.Status.idle, activity=discord.Activity(type=discord.ActivityType.watching, name="my Homies."))
		print(f'I am ready to serve.')

	# Unknown commands
	@commands.Cog.listener()
	async def on_command_error(self, ctx, error):
		if isinstance(error, commands.CommandNotFound):
			await ctx.send('Unknown command used.')

def setup(client):
	client.add_cog(ready(client))