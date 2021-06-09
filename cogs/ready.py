from discord import Activity, ActivityType, Status
from discord.ext import commands, tasks
import os

class ready(commands.Cog):

	def __init__(self,client):
		self.client = client

	# Start
	@commands.Cog.listener()
	async def on_ready(self):
		await self.client.change_presence(status=Status.online, activity=Activity(type=ActivityType.watching, name="andrew than vararuu....maadu pudika poraru.."))
		if ready.leguilds.is_running() is False:
			ready.leguilds.start(self)

	# 
	@tasks.loop(seconds = 1)
	async def leguilds(self):
		clear = lambda: os.system('cls')
		clear()
		print(f'{self.client.user} is connected to the following guild:\n')
		for guild in self.client.guilds:
			print(f'\t{guild.name} (ID: {guild.id}) (Member Count: {guild.member_count})')
			
		print('\nPeople in VC:')
		for guild in self.client.guilds:
			for vc in guild.voice_channels:
				if vc.members!=[]:
					print(f'\t{vc.name}:')
				for members in vc.members:
					str1=f'{members.name} '
					if members.voice.self_mute is False:
						str1 += '🎤'
					else: str1 += '🙊'
					if members.voice.self_deaf is False:
						str1 += '🎧'
					else: str1 += '🙉'
					if members.voice.self_stream is True:
						str1 += ' is live'
					print(f'\t\t{str1}')


	# Unknown commands
	@commands.Cog.listener()
	async def on_command_error(self, ctx, error):
		if isinstance(error, commands.CommandNotFound):
			pass

def setup(client):
	client.add_cog(ready(client))