# Imports
import json
from random import choice, randint

import emoji
from disnake import Client, Message, TextChannel, Webhook
from disnake.ext import commands

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
    if message.author.id == 493025015445454868:
        return False
    if message.content.startswith("pls ") or message.content.startswith("owo "):
        return False
    if message.reference and message.reference.resolved.author.id == 493025015445454868:
        return True
    if any(word in message.content.lower().split() for word in references):
        return True
    return False


async def FetchHook(channel: TextChannel) -> Webhook:
    channel_hooks = await channel.webhooks()
    for webhook in channel_hooks:
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
                return await AndrewWebs.ReplyWebhook(self, message.channel, response)

        # Emoji tings
        if any(
                word in message.content.lower().split()
                for word in emoji.UNICODE_EMOJI_ENGLISH
        ):
            response = choice(["👍", "😂", "🥲", "🤨", "🙄", "😏", "👽", "💩", "🤌", "🤝"])
            return await AndrewWebs.ReplyWebhook(self, message.channel, f"{response * randint(1, 7)}")

        # just mentions
        if not message.attachments:
            for i in references:
                if message.content.lower() == i:
                    response = choice(["No Not ME",
                                       "Yes Tell Me",
                                       "What ?",
                                       "Any Problem ?",
                                       "Why me ?",
                                       "yup yup", ])
                    await AndrewWebs.ReplyWebhook(self, message.channel, response)
                    return

        await message.add_reaction("🤔")
        return await AndrewWebs.ReplyWebhook(self, message.channel, choice(["OK", "k", "mmm", "huh"]))

    async def ReplyWebhook(self, channel: TextChannel, response: str):
        webhook: Webhook = await FetchHook(channel)
        avatar_url: str = self.client.get_user(493025015445454868).display_avatar.url
        await webhook.send(content=response, username="Andrew", avatar_url=avatar_url)


def setup(client: Client):
    client.add_cog(AndrewWebs(client))
