# Imports
import json
from random import choice, randint

import disnake
import emoji
from disnake.ext import commands
from thefuzz import process, fuzz

from EnvVariables import Owner_ID
from assistant import Client, getch_hook

references = ("andrew",
              "santhosh",
              "@andrew",
              "@andrew!#1901",
              "<@!493025015445454868>",
              493025015445454868,
              "<:datsshaawt:804242984383545344>",
              "<:andrew_damnboii:794247753445802004>",)

with open("data/AndrewReplies.json", "r") as replyJSON:
    replies = json.load(replyJSON)
    ALL_QN = []
    for _key in replies:
        ALL_QN.extend(replies[_key]["QN"])
    replyJSON.close()


def checks(message: disnake.Message) -> bool:
    if message.author.bot:
        return False
    if isinstance(message.channel, disnake.DMChannel):
        return False
    if isinstance(message.channel, disnake.Thread):
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


def fetch_reply(qn: str) -> str:
    for key in replies:
        if qn in replies[key]["QN"]:
            return choice(replies[key]["ANS"])


class AndrewWebs(commands.Cog):
    def __init__(self, client: Client):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message) -> None:
        if checks(message) is False:
            return

        # Clean up references
        msg = ""
        for word in message.content.lower().split():
            if word not in references:
                msg += word + " "

        # Fuzzy search for reply
        match, score = process.extractOne(query=msg, choices=ALL_QN,
                                          scorer=fuzz.token_sort_ratio, score_cutoff=60)
        self.client.logger.debug(f"{msg} | {match} | {score}")
        if match is not None:
            await self.reply_hook(message.channel, fetch_reply(match))
            return

        # Emoji tings
        if any(word in message.content.lower().split() for word in emoji.UNICODE_EMOJI_ENGLISH):
            response = choice(["👍", "😂", "🥲", "🤨", "🙄", "😏", "👽", "💩", "🤌", "🤝"])
            await self.reply_hook(message.channel, response=f"{response * randint(1, 7)}")
            return

        # just mentions
        if not message.attachments:
            for i in references:
                if message.content.lower() == i:
                    response = choice(["No Not ME", "Yes Tell Me",
                                       "What ?", "Any Problem ?",
                                       "Why me ?", ])
                    await self.reply_hook(message.channel, response)
                    return

    @staticmethod
    async def reply_hook(channel: disnake.TextChannel, response: str):
        webhook: disnake.Webhook = await getch_hook(channel)
        member: disnake.Member = channel.guild.get_member(Owner_ID)
        await webhook.send(content=response, username=member.display_name, avatar_url=member.display_avatar.url)


def setup(client: Client):
    client.add_cog(AndrewWebs(client))
