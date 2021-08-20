from discord import Activity, ActivityType, Status
import discord.ext.commands as commands

# os, platform
import os, platform

# .env stuff
from olenv import DM_Channel

class ready(commands.Cog):

	def __init__(self,client):
		self.client = client

	async def output(self):
		if platform.system() == 'Windows':
			clear = lambda: os.system('cls')
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
		await ready.output(self)

	@commands.Cog.listener()
	async def on_voice_state_update(self, member, before, after):
		await ready.output(self)

	# Unknown commands
	@commands.Cog.listener()
	async def on_command_error(self, ctx, error):
		if isinstance(error, commands.CommandNotFound):
			await ctx.send(f'{error}.', delete_after=60)
		channel = self.client.get_channel(DM_Channel)
		await channel.send(f'{error}\n`MESSAGE: `{ctx.message.content}')

def setup(client):
	client.add_cog(ready(client))