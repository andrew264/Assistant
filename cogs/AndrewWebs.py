# Imports
import json
from random import choice, randint

import emoji
from disnake import Client, Message, TextChannel, Webhook
from disnake.ext import commands

from EnvVariables import Owner_ID

references = ["andrew",
              "santhosh",
              "@andrew",
              "@andrew!#1901",
              "<@!493025015445454868>",
              493025015445454868,
              "<:datsshaawt:804242984383545344>",
              "<:andrew_damnboii:794247753445802004>", ]

with open("data/AndrewReplies.json", "r") as replyJSON:
    replies = json.load(replyJSON)
    keys = list(replies.keys())
    replyJSON.close()


def checks(message: Message) -> bool:
    if message.author.bot:
        return False
    if message.author.id == Owner_ID:
        return False
    if message.content.startswith("pls ") or message.content.startswith("owo "):
        return False
    if message.reference and message.reference.resolved and message.reference.resolved.author.id == Owner_ID:
        return True
    if any(word in message.content.lower().split() for word in references):
        return True
    return False


async def FetchHook(channel: TextChannel) -> Webhook:
    webhooks = await channel.webhooks()
    for webhook in webhooks:
        if webhook.name == "Reply Hook":
            return webhook
    webhook: Webhook = await channel.create_webhook(name="Reply Hook")
    return webhook


class AndrewWebs(commands.Cog):
    def __init__(self, client: Client):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message: Message) -> None:
        if checks(message) is False:
            return

        # Replies
        for word in message.content.lower().split():
            if word in keys:
                response = replies[word]
                await self.ReplyWebhook(message.channel, response)
                return

        # Emoji tings
        if any(word in message.content.lower().split() for word in emoji.UNICODE_EMOJI_ENGLISH):
            response = choice(["👍", "😂", "🥲", "🤨", "🙄", "😏", "👽", "💩", "🤌", "🤝"])
            await self.ReplyWebhook(message.channel, f"{response * randint(1, 7)}")
            return

        # just mentions
        if not message.attachments:
            for i in references:
                if message.content.lower() == i:
                    response = choice(["No Not ME", "Yes Tell Me",
                                       "What ?", "Any Problem ?",
                                       "Why me ?", "yup yup", ])
                    await self.ReplyWebhook(message.channel, response)
                    return

        await message.add_reaction("🤔")
        await self.ReplyWebhook(message.channel, choice(["😏", "🙄", "mmm", "huh"]))

    async def ReplyWebhook(self, channel: TextChannel, response: str):
        webhook: Webhook = await FetchHook(channel)
        avatar_url: str = self.client.get_user(Owner_ID).display_avatar.url
        await webhook.send(content=response, username="Andrew", avatar_url=avatar_url)


def setup(client: Client):
    client.add_cog(AndrewWebs(client))
