# Imports
from disnake.ext import commands
from disnake import Client, Activity, ActivityType, Status, User, Member, Message, MessageReference
from disnake import Option, OptionChoice, OptionType, ApplicationCommandInteraction

from typing import Optional

from EnvVariables import OWNERID

class Utility(commands.Cog):

	def __init__(self, client: Client):
		self.client = client

	# echo
	@commands.command(hidden=True)
	async def echo(self,ctx: commands.Context, *, args):
		if ctx.author.id != OWNERID :
			await ctx.reply("I am not your Assistant.")
		else:
			await ctx.send(args)
			await ctx.message.delete()

	# ping
	@commands.slash_command(description = "Get Bot's Latency")
	async def ping(self, inter: ApplicationCommandInteraction):
		await inter.response.send_message(f'Client Latency: {round(self.client.latency * 1000)}  ms')

	#Set Status
	@commands.slash_command(description = "Set Bot's Activity", options=[
								 Option(name="state", description="Set Bot's Status", type=OptionType.string, required=True, choices=[
										OptionChoice("Online", 'online'),
										OptionChoice("Idle", 'idle'),
										OptionChoice("Do not Disturb", 'dnd'),
										OptionChoice("Invisible", 'invisible') ]),
								 Option(name="type", description="Set Bot's Activity Type", type=OptionType.integer, required=True, choices=[
										OptionChoice("Playing", 0),
										OptionChoice("Listening", 2),
										OptionChoice("Watching", 3),
										OptionChoice("Streaming", 1) ]),
								 Option(name="name", description="Set Bot's Activity Name", type=OptionType.string)])
	@commands.has_permissions(administrator=True)
	async def status(self, inter: ApplicationCommandInteraction, state: str, type: int, name: str=""):
		await self.client.change_presence(status=Status(state), activity=Activity(type=ActivityType(type), name=name))
		await inter.response.send_message(f'Status set to `{Status(state).name.capitalize()}` and `{ActivityType(type).name.title()}: {name}`', ephemeral=True)

	# clear
	@commands.command(aliases=['delete'])
	@commands.has_permissions(administrator=True)
	async def clear(self, ctx: commands.Context, user: Optional[User], no_of_msgs: Optional[int] = 5):
		if no_of_msgs > 420:
			return await ctx.reply(f'No')
		await ctx.message.delete()
		if user is not None:
			def check(msg: Message):
				return msg.author.id == user.id
			await ctx.channel.purge(limit=no_of_msgs, check=check)
			return await ctx.send(f'`{ctx.author.display_name}` deleted `{user.display_name}\'s` `{no_of_msgs}` message(s).', delete_after=30)
		elif isinstance(ctx.message.reference, MessageReference):
			message: Message = ctx.message.reference.resolved
			await ctx.channel.purge(after=message)
			return await ctx.send(f'`{ctx.author.display_name}` deleted messages till `{message.author.display_name}\'s` message', delete_after=30)
		else:
			await ctx.channel.purge(limit=no_of_msgs)
			return await ctx.send(f'`{ctx.author.display_name}` deleted `{no_of_msgs}` message(s).', delete_after=30)

	@commands.command(aliases=['yeet'])
	@commands.has_permissions(administrator=True)
	async def purge_user(self, ctx: commands.Context, user: Member= None):
		if user is None:
			return await ctx.send("Mention Someone")
		await ctx.send(f'Fetching messages from {ctx.channel.mention}', delete_after=30)
		messages = await ctx.channel.history(limit=69420).flatten()
		await ctx.send(f'Fetched {len(messages)} messages', delete_after=30)
		counter = 0
		for message in messages:
			if message.author.id == user.id or str(user.id) in message.content:
				await message.delete()
				counter +=1
		if counter >0:
			await ctx.send(f'Deleted {counter} messages.', delete_after=30)

def setup(client):
	client.add_cog(Utility(client))