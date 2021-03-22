import discord
import os
import random

from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
OWNERID = int(os.getenv('OWNER_ID'))

from discord.ext import commands
client = commands.Bot(command_prefix='.')

from discord.ext.commands import has_permissions

@client.event
async def on_ready():
	for guild in client.guilds:
		if guild.name == GUILD:
			break
	print(
		f'{client.user} is connected to the following guild:\n'
		f'\t{guild.name}(id: {guild.id})'
	)

# Echo
@client.command()
async def echo(ctx, *, args):
	if ctx.author.id != OWNERID :
		await ctx.reply("I am not your Assistant.,")
	else:
		await ctx.send(args)
		await ctx.message.delete()

# Ping
@client.command()
async def ping(ctx):
	await ctx.send(f'Client Latency: {round(client.latency * 1000)}  ms')

# Clear Command
@client.command()
@has_permissions(manage_messages=True)
async def clear(ctx, amount=5):
	await ctx.channel.purge(limit=amount+1)

# Message Replies
@client.listen('on_message')
async def replies(message):
	if message.author == client.user:
		return 
	hiMsgs = [
		'hi', 'hello', 'allo', 'anyone', 'irukiya' ,'helo', 'yo', 'hey', 'howdy', 'welcome', 'bonjour'
		]

	hiMsgReplys = [
		'https://media1.tenor.com/images/1735ddc5b87d28dd7f6230bd44d7f4e5/tenor.gif?itemid=10231284',
		'https://media1.tenor.com/images/892d25c098ef224ab86a7d624ca64881/tenor.gif?itemid=15372338',
		'https://media1.tenor.com/images/848bc6542afd8caaccf1f3727006cf90/tenor.gif?itemid=10770654',
		'https://media1.tenor.com/images/661e4ed4649950fcbfe6c3c5328025fe/tenor.gif?itemid=10834074',
		'https://media1.tenor.com/images/446c015f3db1d5a14000df0f2f7d7105/tenor.gif?itemid=10124044',
		'https://media1.tenor.com/images/175c66cf1f6f740302e6cdfc90cdbfbb/tenor.gif?itemid=10519859',
		'https://media1.tenor.com/images/fee43b7ecea92ead3c4f3a17d9d94a8d/tenor.gif?itemid=12425836',
		'sollu daw', 'enna da aachi', 'yes tell me', 'mmm', 'hi da'
		]

	byeMsgs = [
		'bye', 'kelamburen', 'poitu varen', 'poren', 'adios', 'goodbye'
		]

	byeMsgReplys = [
		'https://media1.tenor.com/images/c18583dcf6fb22fcf54eb401e18d97d7/tenor.gif?itemid=11772987',
		'bye da'
		]
	if any(word in message.content.lower().split() for word in hiMsgs):
		response = random.choice(hiMsgReplys)
		await message.channel.send(response)
	elif any(word in message.content.lower().split() for word in byeMsgs):
		response = random.choice(byeMsgReplys)
		await message.channel.send(response)

client.run(TOKEN)