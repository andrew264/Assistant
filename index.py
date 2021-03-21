import os
import random
import re

import discord
from dotenv import load_dotenv

from discord.ext import commands
bot = commands.Bot(command_prefix='!')

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

client = discord.Client()

@client.event
async def on_ready():
    for guild in client.guilds:
        if guild.name == GUILD:
            break
    print(
        f'{client.user} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})'
    )

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    hiMsgs = [
    	'hi', 'hello', 'hello there', 'allo', 'anyone', 'irukiya' ,'helo', 'yo'
    ]

    hiMsgReplys = [
    	'Vada noobu', 'sollu daw', 'enna da aachi', 'sollu da ivaneh', 'yes tell me', 'mmm', 'hi da', 'vada pulukesi'
    ]

    if any(word in message.content.lower() for word in hiMsgs):
        response = random.choice(hiMsgReplys)
        await message.channel.send(response)
    elif '!echo' in message.content.lower():
        if message.author.id != 493025015445454868 :
            await message.reply("I am not your Assistant.")
        else:
            await message.channel.send(message.content.replace("!echo ", ""))
            await message.delete()

client.run(TOKEN)