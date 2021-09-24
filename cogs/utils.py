import discord.ext.commands as commands
from olenv import OWNERID
from discord import Activity, ActivityType, Status, User, Message
from discord import errors
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
	@commands.has_permissions(manage_messages=True)
	async def clear(self, ctx: commands.Context, user: Optional[User], no_of_msgs:int = 5):
		if no_of_msgs > 420:
			return await ctx.reply(f'No')
		await ctx.message.delete()
		def check(msg):
			return msg.author.id == user.id
		if user is None:
			await ctx.channel.purge(limit=no_of_msgs)
			await ctx.send(f'`{ctx.author.display_name}` deleted `{no_of_msgs}` message(s).', delete_after=30)
		else:
			await ctx.channel.purge(limit=no_of_msgs, check=check, before=None)
			await ctx.send(f'`{ctx.author.display_name}` deleted `{user.display_name}\'s` `{no_of_msgs}` message(s).', delete_after=30)
	@commands.command(hidden=True)
	@clear.error
	async def clear_error(self, ctx: commands.Context, error: commands.errors):
		if isinstance(error, commands.MissingPermissions):
			await ctx.send('You have no Permission(s).')

	@commands.command(aliases=['yeettill', 'yeetill'])
	@commands.has_permissions(manage_messages=True)
	async def purge_until(self, ctx: commands.Context, message_id: int):
		channel = ctx.message.channel
		try:
			message = await channel.fetch_message(message_id)
		except errors.NotFound:
			return await ctx.send("Message could not be found in this channel")
		await ctx.message.delete()
		await channel.purge(after=message)
		await ctx.send(f'`{ctx.author.display_name}` deleted messages till `{message.content}`', delete_after=30)
		return True

	@commands.command(aliases=['yeetmsg','notme'])
	@commands.has_permissions(manage_messages=True)
	async def purge_msg(self, ctx: commands.Context, string: str, amount: Optional[int] = 10):
		channel = ctx.message.channel
		def check(msg: Message):
			if string.lower() in msg.content.lower(): return True
		await ctx.message.delete()
		await channel.purge(limit=amount, check=check, before=None)
		await ctx.send(f'`{ctx.author.display_name}` deleted `{amount}` {string} message(s).', delete_after=30)

def setup(client):
	client.add_cog(utils(client))