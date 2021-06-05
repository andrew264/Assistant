import discord.ext.commands as commands
from olenv import OWNERID
from discord import Activity, ActivityType, Status, User, Member

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

	# Nickname
	@commands.command(hidden=True,aliases=['nick'])
	async def nickname(self,ctx, member: Member, *, new_nick):
		if ctx.author.guild_permissions.administrator or ctx.author.id == OWNERID :
			await ctx.message.delete()
			old_nick = member.display_name
			await member.edit(nick=new_nick)
			await ctx.send(f'{old_nick} ---> {new_nick}')
		else:
			await ctx.reply("https://media1.tenor.com/images/7bc1dffdde74316e94dcbe421cf2f260/tenor.gif?itemid=8850963")

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

	# Slide into dms
	@commands.command(pass_context = True)
	async def dm(self, ctx, user: User, *, msg:str):
		if ctx.author.id != OWNERID :
			await ctx.reply("I am not your Assistant.")
		else:
			channel = await user.create_dm()
			try:
				await channel.send(msg)
			except Exception: 
				await ctx.send(f'{user} is gei')

def setup(client):
	client.add_cog(utils(client))