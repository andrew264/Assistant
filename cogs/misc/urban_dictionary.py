import random
from typing import Optional
from urllib.parse import quote

import aiohttp
import disnake
from disnake.ext import commands

import assistant
from assistant import colour_gen


class UrbanDictionary:
    def __init__(self):
        self._word: Optional[str] = None
        self.definition: Optional[str] = None
        self.example: Optional[str] = None
        self.result: Optional[str] = None
        self.response: bool = False

    @property
    def url(self):
        return f"https://www.urbandictionary.com/define.php?term={quote(self._word)}"

    @property
    def word(self):
        return self._word.title()

    async def get(self, word: Optional[str]):
        """
        Fetch a definition from Urban Dictionary
        """
        url = f"https://api.urbandictionary.com/v0/define?term={quote(word)}" \
            if word else "https://api.urbandictionary.com/v0/random"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
            await session.close()
        if data is None or any(e in data for e in ('error', 'errors')):
            self.result = 'Error: Invalid input for Urban Dictionary API'
            return
        if len(data['list']) == 0:
            self.result = 'Error: No results found'
            return
        data = random.choice(data['list'])
        self._word = data['word']
        self.definition = data['definition'][-3000:]
        self.example = data['example'][-1000:]
        self.response = True


class Dictionary(commands.Cog):
    def __init__(self, client: assistant.Client):
        self.client = client

    @commands.slash_command()
    async def define(self, inter: disnake.ApplicationCommandInteraction,
                     word: str = commands.Param(description="Enter a word to define", default=None)):
        """
        Fetch definition from Urban Dictionary
        """
        await inter.response.defer()
        urban = UrbanDictionary()
        await urban.get(word)
        if not urban.response:
            await inter.edit_original_message(content=urban.result)
        else:
            embed = disnake.Embed(title=f"Define: {urban.word}",
                                  description=urban.definition, colour=colour_gen(inter.author.id),
                                  url=urban.url)
            embed.add_field(name='Example', value=urban.example)
            await inter.edit_original_message(embed=embed)


def setup(client):
    client.add_cog(Dictionary(client))
