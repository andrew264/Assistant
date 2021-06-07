from random import choice
import discord.ext.commands as commands
from olreplies import *
from olenv import DM_Channel

class replies(commands.Cog):

	def __init__(self,client):
		self.client = client

	# Replies
	@commands.Cog.listener()
	async def on_message(self, message):
		if message.author == self.client.user:
			return
		if message.author.bot: return
		if message.guild is None and not message.author.bot:
			channel = self.client.get_channel(DM_Channel)
			await channel.send(f'UserID: `{message.author.id}`\nMessage Author: `{message.author}`\nMessage:\n`{message.content}`\n──────────────────────────────')
		if any(word in message.content.lower().split() for word in hiMsgs):
			response = choice(hiMsgReplys)
			await message.channel.send(response)
			await self.client.process_commands(message)
		elif any(word in message.content.lower().split() for word in byeMsgs):
			response = choice(byeMsgReplys)
			await message.channel.send(response)
			await self.client.process_commands(message)
		elif any(word in message.content.lower().split() for word in yeahMsgs):
			response = choice(yeahMsgReplys)
			await message.channel.send(response)
			await self.client.process_commands(message)

def setup(client):
	client.add_cog(replies(client))