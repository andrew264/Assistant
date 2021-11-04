# Imports
from disnake.ext import commands
from disnake import Client, Message, TextChannel, Webhook

from random import choice, randint
import emoji, json

references = ['andrew', 'santhosh',
              '@andrew', '@andrew!#1901',
              '<@!493025015445454868>', 493025015445454868,
              '<:datsshaawt:804242984383545344>',
              '<:andrew_damnboii:794247753445802004>']

with open('AndrewReplies.json', 'r') as replyJSON:
    replies = json.load(replyJSON)
    keys = list(replies.keys())
    replyJSON.close()

def checks(message: Message) -> bool:
    if message.author.bot: return False
    if message.author.id == 493025015445454868: return False
    if (message.content.startswith('pls ')
        or message.content.startswith('owo ')):
       return False
    if (message.reference
        and message.reference.resolved.author.id) == 493025015445454868:
        return True
    if any(word in message.content.lower().split() for word in references):
        return True
    return False

class AndrewWebs(commands.Cog):
    def __init__(self, client: Client):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message: Message) -> None:
        if checks(message) is False: return

        # Replies
        for word in message.content.lower().split():
            if word in keys:
                response = replies[word]
                return await AndrewWebs.ReplyWebhook(self,
                                                     message.channel,
                                                     response
                                                     )

        # Emoji tings
        if any(word in message.content.lower().split() for word in emoji.UNICODE_EMOJI_ENGLISH):
            response = choice(['👍','😂','🥲','🤨','🙄','😏','👽','💩','🤌','🤝'])
            return await AndrewWebs.ReplyWebhook(self,
                                                 message.channel,
                                                 f'{response*randint(1,7)}'
                                                 )

        # Handle Server Emojis
        #if any(word in message.content.lower().split() for word in ['<:datsshaawt:804242984383545344>','<:andrew_damnboii:794247753445802004>']):
        #    response = choice(['<:Irlander:849625137380851712>','<:Kadavul:794246857265905698>',
        #                       '<:LEDvaayan:794248183198646273>','<:Walker:849624127417352233>',
        #                       '<:dhaya:844783134985420821>','<:jikki:848302272307003432>',
        #                       '<:junnex:836477586237554688>','<:kadavul:794247073817821234>',
        #                       '<:nani:844457118077550602>','<:saistarz:844454044097052702>',
        #                       '<:sandimama:843566659414654986>','<:scammer_furry:837623485714792478>',
        #                       '<:shield:790871159179837441>','<:sivaop:844444253090611230>',
        #                       '<:sivaL:870967162125303818><:sivaR:870967162674741268>',
        #                       ])
        #    return await AndrewWebs.ReplyWebhook(self, message.channel, response)

        # just mentions
        if message.attachments == []:
            for i in references:
                if message.content.lower() == i:
                    response = choice(['No Not ME', 'Yes Tell Me', 'What ?', 'Any Problem ?', 'Why me ?', 'yup yup'])
                    return await AndrewWebs.ReplyWebhook(self, message.channel, response)

        await message.add_reaction('🤔')
        return await AndrewWebs.ReplyWebhook(self,
                                             message.channel,
                                             choice(["OK", 'k', 'mmm', 'huh'])
                                             )

    async def ReplyWebhook(self, channel: TextChannel, response: str):
        webhook: Webhook = await AndrewWebs.FetchHook(self, channel)
        avatarURL = self.client.get_user(493025015445454868).display_avatar.url
        await webhook.send(content=response,
                           username='Andrew',
                           avatar_url = avatarURL
                           )

    async def FetchHook(self, channel: TextChannel) -> Webhook:
        channel_hooks = await channel.webhooks()
        for webhook in channel_hooks:
            if webhook.name == "Reply Hook":
                return webhook
        webhook: Webhook = await channel.create_webhook(name="Reply Hook")
        return webhook

def setup(client: Client):
    client.add_cog(AndrewWebs(client))