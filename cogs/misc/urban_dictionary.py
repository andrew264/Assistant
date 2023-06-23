import random
from typing import List, Self
from urllib.parse import quote
import re

import aiohttp
import disnake
from disnake.ext import commands

import assistant
from assistant.hooker import getch_hook


class UrbanDictionaryEntry:
    pattern = r"\[([^\]]+)\]"

    def __init__(self, entry_dict: dict):
        self.definition = str(entry_dict.get('definition', 'No definition found.'))
        self.permalink = str(entry_dict.get('permalink', ''))
        self.thumbs_up = int(entry_dict.get('thumbs_up', 0))
        self.author = str(entry_dict.get('author', 'Unknown'))
        self.word = str(entry_dict.get('word', ''))
        self.defid = int(entry_dict.get('defid', 0))
        self.current_vote = str(entry_dict.get('current_vote', ''))
        self.written_on = str(entry_dict.get('written_on', ''))
        self.example = str(entry_dict.get('example', ''))
        self.thumbs_down = int(entry_dict.get('thumbs_down', 0))

    def __lt__(self, other: Self):
        return self.thumbs_up < other.thumbs_up

    def __eq__(self, other: Self):
        return self.defid == other.defid

    def __gt__(self, other: Self):
        return self.thumbs_up > other.thumbs_up

    def __le__(self, other: Self):
        return self.thumbs_up <= other.thumbs_up

    def __ge__(self, other: Self):
        return self.thumbs_up >= other.thumbs_up

    def __ne__(self, other: Self):
        return self.defid != other.defid

    def __repr__(self):
        return f"<UrbanDictionaryEntry defid={self.defid} word={self.word} author={self.author}>"

    def __str__(self):
        return f"{self.word} - {self.author} ({self.thumbs_up} 👍 {self.thumbs_down} 👎)\n{self.definition}\n{self.example}"

    @staticmethod
    def get_url_for(word: str):
        return f"[{word}](https://www.urbandictionary.com/define.php?term={quote(word)})"

    @property
    def get_formatted_definition(self) -> str:
        matches = re.findall(self.pattern, self.definition)
        defn = self.definition
        for match in matches:
            defn = defn.replace(f"[{match}]", self.get_url_for(match))
        return defn

    @property
    def get_formatted_example(self) -> str:
        matches = re.findall(self.pattern, self.example)
        example = self.example
        for match in matches:
            example = example.replace(f"[{match}]", self.get_url_for(match))
        return example

    @property
    def markdown(self):
        return f"# Define: {self.get_url_for(self.word)}\n{self.get_formatted_definition}\n\n## Example:\n_{self.get_formatted_example}_\n\n_{self.thumbs_up}_ 👍 \u2022 _{self.thumbs_down}_ 👎"


class UrbanDictionary:
    def __init__(self, word: str = ''):
        self._word: str = word
        self.response: bool = False
        self.result: List[UrbanDictionaryEntry] = []

    @property
    def url(self):
        return f"https://www.urbandictionary.com/define.php?term={quote(self._word)}"

    @property
    def word(self):
        return self._word.title() if self._word else None

    async def get(self):
        """
        Fetch a definition from Urban Dictionary
        """
        url = f"https://api.urbandictionary.com/v0/define?term={quote(self._word)}" \
            if self._word else "https://api.urbandictionary.com/v0/random"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
            await session.close()
        if data is None or any(e in data for e in ('error', 'errors')):
            return
        if len(data['list']) == 0:
            return
        data = [UrbanDictionaryEntry(data) for data in data['list']]
        data.sort(reverse=True)
        self.result = data
        self.response = True

    async def get_results(self):
        await self.get()
        return self.result


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
        urban = UrbanDictionary(word=word)
        results = await urban.get_results()
        if not urban.response:
            await inter.edit_original_message(content="No results found.")
        else:
            random_result = random.choice(results[:5])
            if len(random_result.markdown) > 2000:
                msgs = random_result.markdown.split('\n\n')
                await inter.edit_original_message(content=msgs[0], suppress_embeds=True)
                webhook = await getch_hook(inter.channel)
                for msg in msgs[1:]:
                    await webhook.send(msg if len(msg) < 2000 else msg[:2000],
                                       username=inter.me.display_name,
                                       avatar_url=inter.me.display_avatar.url,
                                       suppress_embeds=True)
            else:
                await inter.edit_original_message(content=random_result.markdown, suppress_embeds=True)


def setup(client):
    client.add_cog(Dictionary(client))
