# Imports
from disnake import Activity, ActivityType, Status, Client, ApplicationCommandInteraction
from disnake.ext import commands

import os, platform

from EnvVariables import DM_Channel

class Ready(commands.Cog):

	def __init__(self, client: Client):
		self.client = client

	async def Output(self):
		if platform.system() == 'Windows': clear = lambda: os.system('cls')
		else: clear = lambda: os.system('clear')
		clear()
		print(f'{self.client.user} is connected to the following guild:')
		for guild in self.client.guilds:
			print(f'\t{guild.name} (ID: {guild.id}) (Member Count: {guild.member_count})')
		
		print(f'\nClient Latency: {round(self.client.latency * 1000)}  ms')
		print('\nPeople in VC:')
		for guild in self.client.guilds:
			for vc in guild.voice_channels:
				if vc.members!=[]:
					print(f'\t🔊 {vc.name}:')
				for members in vc.members:
					str1=f'{members.display_name}'
					if members.voice.self_mute is True:
						str1 += '🙊'
					if members.voice.self_deaf is True:
						str1 += '🙉'
					if members.voice.self_stream is True:
						str1 += ' is live 🔴'
					print(f'\t\t{str1}')

	# Start
	@commands.Cog.listener()
	async def on_ready(self):
		await self.client.change_presence(status=Status.online, activity=Activity(type=ActivityType.watching, name="yall Homies."))
		await Ready.Output(self)

	@commands.Cog.listener()
	async def on_voice_state_update(self, member, before, after):
		await Ready.Output(self)

	# Unknown commands
	@commands.Cog.listener()
	async def on_command_error(self, ctx: commands.Context, error):
		if isinstance(error, commands.CommandNotFound): return
		elif isinstance(error, commands.MissingPermissions):
			return await ctx.send(error, delete_after=60)
		else: await ctx.send(f'***{error}***')

	# slash errors
	@commands.Cog.listener()
	async def on_slash_command_error(self, inter: ApplicationCommandInteraction, error: commands.CommandError):
		for error in error.args:
			await inter.response.send_message(f"```{error}```", ephemeral=True)

def setup(client):
	client.add_cog(Ready(client))