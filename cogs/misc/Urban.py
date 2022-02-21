from typing import Optional
from urllib.parse import quote

import aiohttp
import disnake
from disnake.ext import commands

import assistant


class UrbanDefinition:
    def __init__(self, _word: str, definition: str, example: str, permalink: str):
        self.word = _word
        self.definition = definition
        self.example = example
        self.url = permalink


class UrbanDictionary(commands.Cog):
    def __init__(self, client: assistant.Client):
        self.client = client

    async def get_urban_definition(self, word: Optional[str]) -> str | UrbanDefinition:
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
            return 'Invalid input for Urban Dictionary API'
        if len(data['list']) == 0:
            return 'No results found'
        return UrbanDefinition(data['list'][0]['word'],
                               data['list'][0]['definition'],
                               data['list'][0]['example'],
                               url)

    @commands.slash_command()
    async def define(self, inter: disnake.ApplicationCommandInteraction,
                     word: str = commands.Param(description="Enter a word to define", default=None)):
        """
        Fetch a definition from Urban Dictionary
        """
        await inter.response.defer()
        definition = await self.get_urban_definition(word)
        if isinstance(definition, str):
            await inter.edit_original_message(content=definition)
        else:
            embed = disnake.Embed(title=f"Define: {definition.word.title()}",
                                  description=definition.definition, colour=disnake.Colour.blurple(),
                                  url=definition.url)
            embed.add_field(name='Example', value=definition.example)
            await inter.edit_original_message(embed=embed)


def setup(client):
    client.add_cog(UrbanDictionary(client))
