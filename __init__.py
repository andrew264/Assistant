import os
import random

import discord
from dotenv import load_dotenv

from discord.ext import commands
bot = commands.Bot(command_prefix='!')

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
OWNERID = int(os.getenv('OWNER_ID'))



client = discord.Client()

@client.event
async def on_ready():
    for guild in client.guilds:
        if guild.name == GUILD:
            break
    print(
        f'{client.user} is connected to the following guild:\n'
        f'\t{guild.name}(id: {guild.id})'
    )

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    hiMsgs = [
    'hi', 'hello', 'hello there', 'allo', 'anyone', 'irukiya' ,'helo', 'yo'
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
    'bye', 'kelamburen', 'poitu varen', 'poren'
    ]

    byeMsgReplys = [
    'https://media1.tenor.com/images/c18583dcf6fb22fcf54eb401e18d97d7/tenor.gif?itemid=11772987',
    'bye da'
    ]
    if any(word in message.content.lower() for word in hiMsgs):
        response = random.choice(hiMsgReplys)
        await message.channel.send(response)
    elif any(word in message.content.lower() for word in byeMsgs):
        response = random.choice(byeMsgReplys)
        await message.channel.send(response)
    elif '!echo' in message.content.lower():
        if message.author.id != OWNERID :
            await message.reply("I am not your Assistant.")
        else:
            await message.channel.send(message.content.replace("!echo ", ""))
            await message.delete()

client.run(TOKEN)