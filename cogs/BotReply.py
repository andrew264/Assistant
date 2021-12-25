# Imports
from random import choice

import disnake
from disnake import (
    Message,
    Client,
    TextChannel,
    Webhook,
)
from disnake.ext import commands

hiMsgs = ["hi",
          "hello",
          "allo",
          "anyone",
          "irukiya",
          "helo",
          "halo",
          "alo",
          "yo",
          "hey",
          "howdy",
          "welcome",
          "bonjour",
          "hola",
          "hii",
          "hiii",
          "hlo",
          "hai", ]
hiMsgReply = ["https://media1.tenor.com/images/1735ddc5b87d28dd7f6230bd44d7f4e5/tenor.gif?itemid=10231284",
              "https://media1.tenor.com/images/892d25c098ef224ab86a7d624ca64881/tenor.gif?itemid=15372338",
              "https://media1.tenor.com/images/848bc6542afd8caaccf1f3727006cf90/tenor.gif?itemid=10770654",
              "https://media1.tenor.com/images/661e4ed4649950fcbfe6c3c5328025fe/tenor.gif?itemid=10834074",
              "https://media1.tenor.com/images/446c015f3db1d5a14000df0f2f7d7105/tenor.gif?itemid=10124044",
              "https://media1.tenor.com/images/175c66cf1f6f740302e6cdfc90cdbfbb/tenor.gif?itemid=10519859",
              "https://media1.tenor.com/images/fee43b7ecea92ead3c4f3a17d9d94a8d/tenor.gif?itemid=12425836",
              "sollu daw",
              "enna da aachi",
              "yes tell me",
              "mmm",
              "hi da", ]

byeMsgs = ["bye",
           "kelamburen",
           "poitu varen",
           "poren",
           "adios",
           "goodbye",
           "night",
           "gn", ]
byeMsgReply = ["https://media1.tenor.com/images/c18583dcf6fb22fcf54eb401e18d97d7/tenor.gif?itemid=11772987",
               "bye da", ]

yeahMsgs = ["yeah", "boi", "boii", "yes", "s", "aama"]
yeahMsgReply = ["https://media1.tenor.com/images/a7cdeb1036b54acce7c624f999989a1e/tenor.gif?itemid=17305845",
                "https://media1.tenor.com/images/f35c5a5b72f78a56c7680873206a3fbf/tenor.gif?itemid=6042030",
                "https://tenor.com/view/nodding-yeah-boy-longest-yeah-boy-man-beard-gif-7733818",
                "https://tenor.com/view/yes-baby-goal-funny-face-gif-13347383",
                "https://tenor.com/view/pedro-approves-pedrorc-pedroredcerberus-yes-agree-gif-11599348", ]


async def FetchHook(channel: TextChannel) -> Webhook:
    channel_hooks = await channel.webhooks()
    for webhook in channel_hooks:
        if webhook.name == "Reply Hook":
            return webhook

    webhook: Webhook = await channel.create_webhook(name="Reply Hook")
    return webhook


class BotReply(commands.Cog):
    def __init__(self, client: Client):
        self.client = client

    # Replies
    @commands.Cog.listener()
    async def on_message(self, message: Message) -> None:
        if message.author == self.client.user:
            return
        if message.author.bot:
            return
        if isinstance(message.channel, disnake.DMChannel):
            return
        if isinstance(message.channel, disnake.Thread):
            return
        if any(word in message.content.lower().split() for word in hiMsgs):
            response = choice(hiMsgReply)
            return await BotReply.ReplyWebhook(self, message.channel, response)
        elif any(word in message.content.lower().split() for word in byeMsgs):
            response = choice(byeMsgReply)
            return await BotReply.ReplyWebhook(self, message.channel, response)
        elif any(word in message.content.lower().split() for word in yeahMsgs):
            response = choice(yeahMsgReply)
            return await BotReply.ReplyWebhook(self, message.channel, response)

    async def ReplyWebhook(self, channel: TextChannel, response: str) -> None:
        webhook: Webhook = await FetchHook(channel)
        member = self.client.get_user(493025015445454868)
        if member:
            display_name = member.display_name
            avatar_url = member.display_avatar.url
            await webhook.send(content=response, username=display_name, avatar_url=avatar_url)


def setup(client):
    client.add_cog(BotReply(client))
