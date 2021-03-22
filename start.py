import discord
import os

from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
OWNERID = int(os.getenv('OWNER_ID'))

from discord.ext import commands
client = commands.Bot(command_prefix='.')

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
			await ctx.send('\N{OK HAND SIGN}')
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
			await ctx.send('\N{OK HAND SIGN}')
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
			await ctx.send('\N{OK HAND SIGN}')
		else:
			await ctx.send('\N{PISTOL} U no Admin.')

for filename in os.listdir('./cogs'):
	if filename.endswith('.py'):
		client.load_extension(f'cogs.{filename[:-3]}')

client.run(TOKEN)