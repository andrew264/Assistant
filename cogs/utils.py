import discord.ext.commands as commands
from olenv import OWNERID
from discord import Activity, ActivityType, Status, User, Member, Message, MessageReference
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
	@commands.command(pass_context=True)
	async def status(self, ctx, state, type, *, name):
		if ctx.author.id != OWNERID:
			await ctx.reply("You don't have permission")
		else:
			if state == 'idle':
				A=Status.idle
			elif state == 'online':
				A=Status.online
			elif state == 'dnd':
				A=Status.dnd
			elif state == 'offline':
				A=Status.offline
			else:
				return await ctx.send(f'Invalid status `{state}`.')
			if type == 'play':
				B=ActivityType.playing
			elif type == 'stream':
				B=ActivityType.streaming
			elif type == 'listen':
				B=ActivityType.listening
			elif type == 'watch':
				B=ActivityType.watching
			else:
				return await ctx.send(f'Invalid Activity Type `{type}`.')
			await self.client.change_presence(status=A, activity=Activity(type=B, name=name))
			await ctx.send(f'Status set to `{state}` and `{type.title()}ing: {name}`')

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