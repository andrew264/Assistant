# Imports
from disnake.ext import commands
from disnake import Message, Client

from random import choice

from ReplyMsgs import *

class BotReply(commands.Cog):

	def __init__(self, client: Client):
		self.client = client

	# Replies
	@commands.Cog.listener()
	async def on_message(self, message: Message):
		if message.author == self.client.user: return
		if message.author.bot: return
		if any(word in message.content.lower().split() for word in hiMsgs):
			response = choice(hiMsgReplys)
			return await message.channel.send(response)
		elif any(word in message.content.lower().split() for word in byeMsgs):
			response = choice(byeMsgReplys)
			return await message.channel.send(response)
		elif any(word in message.content.lower().split() for word in yeahMsgs):
			response = choice(yeahMsgReplys)
			return await message.channel.send(response)

def setup(client):
	client.add_cog(BotReply(client))