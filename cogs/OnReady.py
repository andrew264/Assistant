# Imports
from disnake.ext import commands
from disnake import (
	Activity,
	ActivityType,
	ApplicationCommandInteraction,
	Client,
	Color,
	CustomActivity,
	Embed,
	Member,
	Spotify,
	Status,
	)

import os, platform, traceback

from EnvVariables import DM_Channel

old_str1 = ''

def fancy_traceback(exc: Exception) -> str:
    text = ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    return f"```py\n{text[-4086:]}\n```"

# Show Clients
def AvailableClients(user: Member) -> str:
	clients = []
	if user.desktop_status.name != 'offline':
		clients.append('Desktop')
	if user.mobile_status.name != 'offline':
		clients.append('Mobile')
	if user.web_status.name != 'offline':
		clients.append('Web')
	if clients == []: clients.append('Offline')
	if user.raw_status == 'online': value = "🟢"
	elif user.raw_status == 'idle': value = "🌙"
	elif user.raw_status == 'dnd': value = "⛔"
	elif user.raw_status == 'offline': value = "🔘"
	return f"{value} {', '.join(clients)}"

# Custom Act
def CustomActVal(activity: CustomActivity) -> str:
	value: str = 'Status: '
	if activity.emoji is not None: value += str(activity.emoji)
	if activity.name is not None: value += activity.name
	return value

class Ready(commands.Cog):

	def __init__(self, client: Client):
		self.client = client

	async def Output(self) -> None:
		global old_str1
		str1 = Ready.printstuff(self)
		if old_str1 != str1:
			if platform.system() == 'Windows': clear = lambda: os.system('cls')
			else: clear = lambda: os.system('clear')
			clear()
			print(str1)
			old_str1 = str1

	# Print Text Generator
	def printstuff(self) -> str:
		str1 = f'{self.client.user} is connected to the following guild:'
		for guild in self.client.guilds:
			str1 += f'\n\t{guild.name} (ID: {guild.id}) (Member Count: {guild.member_count})'
		str1 += f'\n\nClient Latency: {round(self.client.latency * 1000)}  ms'
		str1 += '\n\nPeople in VC:\n'
		for guild in self.client.guilds:
			for vc in guild.voice_channels:
				if vc.members: str1 += f'\t🔊 {vc.name}:\n'
				for member in vc.members:
					str1+=f'\t\t{member.display_name}'
					if member.voice.self_mute or member.voice.mute: str1 += '🙊'
					if member.voice.self_deaf or member.voice.deaf: str1 += '🙉'
					if member.voice.self_stream: str1 += ' is live 🔴'
					if member.voice.self_video : str1 += '📷'
					for activity in member.activities:
						str1 += f'\n\t\t\t> '
						if isinstance(activity, Spotify):
							str1 += f"Listening to {activity.title} by {', '.join(activity.artists)}"
						elif isinstance(activity, CustomActivity):
							str1 += CustomActVal(member.activity)
						else:
							str1 += f'Playing {activity.name}'
					str1 += f'\n\t\t\t> {AvailableClients(member)}\n'
		return str1

	# Start
	@commands.Cog.listener()
	async def on_ready(self) -> None:
		await self.client.change_presence(status=Status.online, activity=Activity(type=ActivityType.watching, name="yall Homies."))
		await Ready.Output(self)

	@commands.Cog.listener()
	async def on_voice_state_update(self, member, before, after) -> None:
		await Ready.Output(self)

	@commands.Cog.listener()
	async def on_presence_update(self, before, after) -> None:
		await Ready.Output(self)

	# Unknown commands
	@commands.Cog.listener()
	async def on_command_error(
		self,
		ctx: commands.Context,
		error: commands.CommandError
		) -> None:
		if isinstance(error, commands.CommandNotFound): return
		elif isinstance(error, commands.MissingPermissions):
			await ctx.send(error, delete_after=60)
			return
		elif isinstance(error, commands.NotOwner):
			await ctx.send("🚫 You can\'t do that.", delete_after=60)
			return
		elif isinstance(error, commands.UserInputError):
			await ctx.send(f'Error: Invalid {error.args[0]} Argument.')
			return
		elif isinstance(error, commands.CheckFailure):
			await ctx.send(f'***{error}***')
			return
		else:
			await ctx.send(f'***{error}***')
			channel = self.client.get_channel(DM_Channel)
			embed = Embed(
				title=f"Command `{ctx.command}` failed due to `{error}`",
				description=fancy_traceback(error),
				color=Color.red())
			await channel.send(embed=embed)

	# slash errors
	@commands.Cog.listener()
	async def on_slash_command_error(
		self,
		inter: ApplicationCommandInteraction,
		error: commands.CommandError
		) -> None:
		if isinstance(error, commands.NotOwner):
			return await inter.response.send_message("🚫 You can\'t do that.", ephemeral=True)
		elif isinstance(error, commands.MissingPermissions):
			return await inter.response.send_message(error, ephemeral=True)
		else:
			channel = self.client.get_channel(DM_Channel)
			embed = Embed(
				title=f"Command `{inter.application_command.name}` failed due to `{error}`",
				description=fancy_traceback(error),
				color=Color.red())
			await channel.send(embed=embed)

	# Message Context Error
	@commands.Cog.listener()
	async def on_message_command_error(
		self,
		inter: ApplicationCommandInteraction,
		error: commands.CommandError
		) -> None:
		if isinstance(error, commands.NotOwner):
			return await inter.response.send_message("🚫 You can\'t do that.", ephemeral=True)
		elif isinstance(error, commands.MissingPermissions):
			return await inter.response.send_message(error, ephemeral=True)
		else:
			channel = self.client.get_channel(DM_Channel)
			embed = Embed(
				title=f"Command `{inter.application_command.name}` failed due to `{error}`",
				description=fancy_traceback(error),
				color=Color.red())
			await channel.send(embed=embed)

	# User Context Error
	@commands.Cog.listener()
	async def on_user_command_error(
		self,
		inter: ApplicationCommandInteraction,
		error: commands.CommandError
		) -> None:
		if isinstance(error, commands.NotOwner):
			return await inter.response.send_message("🚫 You can\'t do that.", ephemeral=True)
		elif isinstance(error, commands.MissingPermissions):
			return await inter.response.send_message(error, ephemeral=True)
		else:
			channel = self.client.get_channel(DM_Channel)
			embed = Embed(
				title=f"Command `{inter.application_command.name}` failed due to `{error}`",
				description=fancy_traceback(error),
				color=Color.red())
			await channel.send(embed=embed)

def setup(client):
	client.add_cog(Ready(client))