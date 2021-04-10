from random import choice
import discord
from discord.ext import commands
from olreplies import *

class replies(commands.Cog):

	def __init__(self,client):
		self.client = client

	# Replies
	@commands.Cog.listener()
	async def on_message(self, message):
		if message.author == self.client.user:
			return
		if any(word in message.content.lower().split() for word in hiMsgs):
			response = choice(hiMsgReplys)
			await message.channel.send(response)
			await self.client.process_commands(message)
		elif any(word in message.content.lower().split() for word in byeMsgs):
			response = choice(byeMsgReplys)
			await message.channel.send(response)
			await self.client.process_commands(message)

def setup(client):
	client.add_cog(replies(client))