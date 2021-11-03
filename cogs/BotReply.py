# Imports
import disnake
from disnake.ext import commands
from disnake import (
	Message,
	Client,
	TextChannel,
	Webhook,
	)

from random import choice

from ReplyMsgs import *

class BotReply(commands.Cog):

	def __init__(self, client: Client):
		self.client = client

	# Replies
	@commands.Cog.listener()
	async def on_message(self, message: Message) -> None:
		if message.author == self.client.user: return
		if message.author.bot: return
		if isinstance(message.channel, disnake.DMChannel): return
		if isinstance(message.channel, disnake.Thread): return
		if any(word in message.content.lower().split() for word in hiMsgs):
			response = choice(hiMsgReplys)
			return await BotReply.ReplyWebhook(self, message.channel, response)
		elif any(word in message.content.lower().split() for word in byeMsgs):
			response = choice(byeMsgReplys)
			return await BotReply.ReplyWebhook(self, message.channel, response)
		elif any(word in message.content.lower().split() for word in yeahMsgs):
			response = choice(yeahMsgReplys)
			return await BotReply.ReplyWebhook(self, message.channel, response)

	async def ReplyWebhook(self, channel: TextChannel, response: str) -> None:
		webhook: Webhook = await BotReply.FetchHook(self, channel)
		member = self.client.get_user(493025015445454868)
		if member:
			disply_name = member.display_name
			avatarURL = member.display_avatar.url
			await webhook.send(
				content=response,
				username=disply_name,
				avatar_url=avatarURL
				)

	async def FetchHook(self, channel: TextChannel) -> Webhook:
		channel_hooks = await channel.webhooks()
		for webhook in channel_hooks:
			if webhook.name == "Reply Hook":
				return webhook

		webhook: Webhook = await channel.create_webhook(name="Reply Hook")
		return webhook

def setup(client):
	client.add_cog(BotReply(client))