import discord.ext.commands as commands
from olenv import OWNERID
from discord import Activity, ActivityType, Status, User, Member, Message, MessageReference
import dislash
from dislash import Option, OptionChoice, OptionType, SlashInteraction
from dislash.application_commands import slash_client
from typing import Optional

class utils(commands.Cog):

	def __init__(self,client):
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
	@slash_client.slash_command(description = "Get Bot's Latency")
	async def ping(self, ctx: commands.Context):
		await ctx.send(f'Client Latency: {round(self.client.latency * 1000)}  ms')

	#Set Status
	@slash_client.slash_command(description = "Set Bot's Activity", options=[
								 Option(name="state", description="Set Bot's Status", type=OptionType.STRING, required=True, choices=[
										OptionChoice("Online", Status.online),
										OptionChoice("Idle", Status.idle),
										OptionChoice("Do not Disturb", Status.dnd),
										OptionChoice("Offline", Status.offline) ]),
								 Option(name="type", description="Set Bot's Activity Type", type=OptionType.STRING, required=True, choices=[
										OptionChoice("Playing", ActivityType.playing),
										OptionChoice("Listening", ActivityType.listening),
										OptionChoice("Watching", ActivityType.watching),
										OptionChoice("Streaming", ActivityType.streaming) ]),
								 Option(name="name", description="Set Bot's Activity Name", type=OptionType.STRING)])
	@dislash.has_permissions(administrator=True)
	async def status(self, inter: SlashInteraction, state: Status, type: ActivityType, name: str=""):
		await self.client.change_presence(status=state, activity=Activity(type=type, name=name))
		await inter.respond(f'Status set to `{state.name.capitalize()}` and `{type.name.title()}: {name}`', ephemeral=True)

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
	@commands.has_permissions(manage_messages=True)
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
	client.add_cog(utils(client))