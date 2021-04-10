import discord
from discord.ext import commands
from olreplies import *
from olenv import *

class utils(commands.Cog):

	def __init__(self,client):
		self.client = client

	# echo
	@commands.command(hidden=True)
	async def echo(self,ctx,*,args):
		if ctx.author.id != OWNERID :
			await ctx.reply("I am not your Assistant.")
		else:
			await ctx.send(args)
			await ctx.message.delete()

	# ping
	@commands.command()
	async def ping(self,ctx):
		await ctx.send(f'Client Latency: {round(self.client.latency * 1000)}  ms')

	# clear
	@commands.command()
	@commands.has_permissions(manage_messages=True)
	async def clear(self, ctx, amount=5):
		await ctx.channel.purge(limit=amount+1)
	@commands.command(hidden=True)
	@clear.error
	async def clear_error(self, ctx, error):
		if isinstance(error, commands.MissingPermissions):
			await ctx.send('You have no Permission(s).')

	#Set Status
	@commands.command(pass_context=True)
	async def status(self, ctx, state, type, *, name):
		if ctx.author.id != OWNERID:
			await ctx.reply("You don't have permission")
		else:
			if state == 'idle':
				A=discord.Status.idle
			elif state == 'online':
				A=discord.Status.online
			elif state == 'dnd':
				A=discord.Status.dnd
			elif state == 'offline':
				A=discord.Status.offline
			else:
				return await ctx.send(f'Invalid status `{state}`.')
			if type == 'play':
				B=discord.ActivityType.playing
			elif type == 'stream':
				B=discord.ActivityType.streaming
			elif type == 'listen':
				B=discord.ActivityType.listening
			elif type == 'watch':
				B=discord.ActivityType.watching
			else:
				return await ctx.send(f'Invalid Activity Type `{type}`.')
			await self.client.change_presence(status=A, activity=discord.Activity(type=B, name=name))
			await ctx.send(f'Status set to `{state}` and `{type.title()}ing: {name}`')

def setup(client):
	client.add_cog(utils(client))