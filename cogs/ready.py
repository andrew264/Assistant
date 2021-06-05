from discord import Activity, ActivityType, Status
import discord.ext.commands as commands

class ready(commands.Cog):

	def __init__(self,client):
		self.client = client

	# Start
	@commands.Cog.listener()
	async def on_ready(self):
		await self.client.change_presence(status=Status.idle, activity=Activity(type=ActivityType.watching, name="my Homies."))
		print(f'{self.client.user} is connected to the following guild:\n')
		for guild in self.client.guilds:
			print(f'\t{guild.name}(id: {guild.id})')

	# Unknown commands
	@commands.Cog.listener()
	async def on_command_error(self, ctx, error):
		if isinstance(error, commands.CommandNotFound):
			pass

def setup(client):
	client.add_cog(ready(client))