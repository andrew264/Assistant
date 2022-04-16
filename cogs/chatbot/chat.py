# Imports
from typing import Optional

import disnake
from disnake.ext import commands
import random
import json

import torch

from EnvVariables import Owner_ID
from assistant import Client, getch_hook
from cogs.chatbot.model import NeuralNet
from cogs.chatbot.nltk_utils import bag_of_words, tokenize

data = torch.load('data/data.pth')

input_size = data["input_size"]
hidden_size = data["hidden_size"]
output_size = data["output_size"]
all_words = data['all_words']
tags = data['tags']
model_state = data["model_state"]

model = NeuralNet(input_size, hidden_size, output_size).to(torch.device('cpu'))
model.load_state_dict(model_state)
model.eval()

with open('data/intents.json', 'r') as json_data:
    intents = json.load(json_data)

REFERENCES = ("andrew",
              "santhosh",
              "@andrew",
              "@andrew!#1901",
              "<@!493025015445454868>",
              "<@493025015445454868>",
              Owner_ID,
              "<:datsshaawt:804242984383545344>",
              "<:andrew_damnboii:794247753445802004>",)


class Chat(commands.Cog):
    def __init__(self, client: Client):
        self.client = client

    @staticmethod
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
        if any(word in message.content.lower().split() for word in REFERENCES):
            return True
        return False

    @staticmethod
    def _get_response(sentence: str) -> Optional[str]:
        sentence = tokenize(sentence)
        X = bag_of_words(sentence, all_words)
        X = X.reshape(1, X.shape[0])
        X = torch.from_numpy(X).to(torch.device('cpu'))

        output = model(X)
        _, predicted = torch.max(output, dim=1)

        tag = tags[predicted.item()]

        probs = torch.softmax(output, dim=1)
        prob = probs[0][predicted.item()]
        if prob.item() > 0.90:
            for intent in intents['intents']:
                if tag == intent["tag"]:
                    return random.choice(intent['responses'])
        return None

    @commands.Cog.listener('on_message')
    async def chat_bot_response(self, message: disnake.Message):
        if self.checks(message) is False:
            return
        self.client.logger.debug(f"{message.author} said: {message.content}")
        # Clean up references
        msg = ""
        for word in message.content.lower().split():
            if word not in REFERENCES:
                msg += word + " "
        response = self._get_response(msg)
        if response:
            self.client.logger.debug(f"Chatbot: {response}")
            await self.reply_hook(message.channel, response)

    @staticmethod
    async def reply_hook(channel: disnake.TextChannel, response: str):
        webhook: disnake.Webhook = await getch_hook(channel)
        member: disnake.Member = channel.guild.get_member(Owner_ID)
        await webhook.send(content=response, username=member.display_name, avatar_url=member.display_avatar.url)


def setup(client):
    client.add_cog(Chat(client))
