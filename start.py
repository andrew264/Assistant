from os import listdir
from olenv import OWNERID, TOKEN

import discord.ext.commands as commands
client = commands.Bot(command_prefix=commands.when_mentioned_or('.'),description='Andrew\'s Assistant',help_command=None)

@client.command(hidden=True)
async def load(ctx, extension):
	try:
		if ctx.message.author.id == OWNERID :
			client.load_extension(f'cogs.{extension}')
	except Exception as e:
		await ctx.send('\N{PISTOL}')
		await ctx.send('{}: {}'.format(type(e).__name__, e))
	else:
		if ctx.message.author.id == OWNERID :
			await ctx.message.add_reaction('👌')
		else:
			await ctx.send('\N{PISTOL} U no Admin.')

@client.command(hidden=True)
async def unload(ctx, extension):
	try:
		if ctx.message.author.id == OWNERID :
			client.unload_extension(f'cogs.{extension}')
	except Exception as e:
		await ctx.send('\N{PISTOL}')
		await ctx.send('{}: {}'.format(type(e).__name__, e))
	else:
		if ctx.message.author.id == OWNERID :
			await ctx.message.add_reaction('👌')
		else:
			await ctx.send('\N{PISTOL} U no Admin.')

@client.command(hidden=True)
async def reload(ctx, extension):
	try:
		if ctx.message.author.id == OWNERID :
			client.unload_extension(f'cogs.{extension}')
			client.load_extension(f'cogs.{extension}')
	except Exception as e:
		await ctx.send('\N{PISTOL}')
		await ctx.send('{}: {}'.format(type(e).__name__, e))
	else:
		if ctx.message.author.id == OWNERID :
			await ctx.message.add_reaction('👌')
		else:
			await ctx.send('\N{PISTOL} U no Admin.')

for filename in listdir('./cogs'):
	if filename.endswith('.py'):
		client.load_extension(f'cogs.{filename[:-3]}')

client.run(TOKEN)