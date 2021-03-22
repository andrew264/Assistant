import discord
from discord.ext import commands

from discord.ext.commands import has_permissions

class utils(commands.Cog):

	def __init__(self,client):
		self.client = client

	# echo
	@commands.command(hidden=True)
	async def echo(self,ctx,*,args):
		if ctx.author.id != ctx.guild.owner_id :
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
	@has_permissions(manage_messages=True)
	async def clear(self, ctx, amount=5):
		await ctx.channel.purge(limit=amount+1)
	@commands.command(hidden=True)
	@clear.error
	async def clear_error(self, ctx, error):
		if isinstance(error, commands.MissingPermissions):
			await ctx.send('You have no Permission(s).')

def setup(client):
	client.add_cog(utils(client))