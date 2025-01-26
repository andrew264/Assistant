import random
import re
from typing import Any, Dict, List, Self
from urllib.parse import quote

import aiohttp
import discord
from cachetools import TTLCache
from discord import app_commands
from discord.ext import commands

from assistant import AssistantBot

urban_cache = TTLCache(maxsize=500, ttl=10800)
LINK_PATTERN = re.compile(r"\[([^\]]+)\]")
UD_API_RANDOM = "https://api.urbandictionary.com/v0/random"
UD_BASE_URL = "https://www.urbandictionary.com/define.php?term={}"


class UrbanDictionaryEntry:
    """Represents an Urban Dictionary entry with formatted output capabilities."""

    def __init__(self, entry_data: Dict[str, Any]):
        self.definition = str(entry_data.get("definition", "No definition found."))
        self.example = str(entry_data.get("example", ""))
        self.word = str(entry_data.get("word", ""))
        self.author = str(entry_data.get("author", "Unknown"))
        self.permalink = str(entry_data.get("permalink", ""))
        self.thumbs_up = int(entry_data.get("thumbs_up", 0))
        self.thumbs_down = int(entry_data.get("thumbs_down", 0))
        self.defid = int(entry_data.get("defid", 0))
        self.written_on = str(entry_data.get("written_on", ""))

    def __repr__(self) -> str:
        return f"<UrbanDictionaryEntry defid={self.defid} word='{self.word}'>"

    def __str__(self) -> str:
        return (f"{self.word} - {self.author} "
                f"({self.thumbs_up} 👍 / {self.thumbs_down} 👎)\n"
                f"{self.definition}\n\n"
                f"Example: {self.example}")

    def __eq__(self, other: Self) -> bool:
        return self.defid == other.defid

    def __lt__(self, other: Self) -> bool:
        return self.thumbs_up < other.thumbs_up

    def __le__(self, other: Self) -> bool:
        return self.thumbs_up <= other.thumbs_up

    def __gt__(self, other: Self) -> bool:
        return self.thumbs_up > other.thumbs_up

    def __ge__(self, other: Self) -> bool:
        return self.thumbs_up >= other.thumbs_up

    @staticmethod
    def _format_links(text: str) -> str:
        """Convert [terms] in text to Urban Dictionary markdown links."""
        return LINK_PATTERN.sub(lambda m: f"[{m.group(1)}]({UD_BASE_URL.format(quote(m.group(1)))})", text)

    @property
    def formatted_definition(self) -> str:
        """Definition with embedded markdown links."""
        return self._format_links(self.definition)

    @property
    def formatted_example(self) -> str:
        """Example text with embedded markdown links."""
        return self._format_links(self.example)

    @property
    def markdown(self) -> str:
        """Complete entry formatted in markdown."""
        return (f"# Define: [{self.word}]({self.permalink})\n\n"
                f"{self.formatted_definition}\n\n"
                f"*Example:*\n{self.formatted_example}\n\n"
                f"{self.thumbs_up} 👍  \u2022  {self.thumbs_down} 👎\n")


class UrbanDictionaryClient:
    """Client for fetching Urban Dictionary entries with caching support."""

    def __init__(self, word: str = ""):
        self.search_term = word.strip()
        self.results: List[UrbanDictionaryEntry] = []

    @property
    def _cache_key(self) -> str:
        return f"urban:{self.search_term}"

    @property
    def _api_url(self) -> str:
        if self.search_term:
            return f"https://api.urbandictionary.com/v0/define?term={quote(self.search_term)}"
        return UD_API_RANDOM

    async def fetch(self) -> bool:
        """Fetch entries from API or cache. Returns success status."""
        if self.search_term:
            if cached := urban_cache.get(self._cache_key):
                self.results = cached
                return True

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self._api_url) as response:
                    data = await response.json()
        except (aiohttp.ClientError, ValueError):
            return False

        if not isinstance(data.get("list"), list) or len(data["list"]) == 0:
            return False

        entries = [UrbanDictionaryEntry(entry) for entry in data["list"]]
        self.results = sorted(entries, reverse=True)

        if self.search_term:
            urban_cache[self._cache_key] = self.results

        return True

    def top_results(self, count: int = 5) -> List[UrbanDictionaryEntry]:
        """
        Get top N entries sorted by thumbs up votes.
        """
        return self.results[:count]


class Dictionary(commands.Cog):
    def __init__(self, bot: AssistantBot):
        self.bot = bot

    async def get_webhook(self, channel: discord.TextChannel):
        assert self.bot.user
        webhooks = await channel.webhooks()
        webhook = None
        for wh in webhooks:
            assert wh.user
            if wh.user.id == self.bot.user.id:
                webhook = wh
                break
        if webhook is None:
            webhook = await channel.create_webhook(name='Assistant', avatar=await self.bot.user.display_avatar.read())
        return webhook

    @commands.hybrid_command(name='define', aliases=['def', 'dictionary', 'dict'], description='Define a word')
    @app_commands.describe(word='The word to define')
    async def define(self, ctx: commands.Context, *, word: str = ''):
        await ctx.defer()
        client = UrbanDictionaryClient("yeet")
        await client.fetch()
        results = client.top_results()
        if not results:
            await ctx.send(f"No definition found for {word}.")
            return
        else:
            random_result = random.choice(results)
            if len(random_result.markdown) > 2000:
                msgs = random_result.markdown.split('\n\n')
                await ctx.send(content=msgs[0][:2000], suppress_embeds=True)
                if not isinstance(ctx.channel, discord.TextChannel):
                    return
                webhook = await self.get_webhook(ctx.channel)
                for msg in msgs[1:]:
                    await webhook.send(msg[:2000], username=ctx.me.display_name, avatar_url=ctx.me.display_avatar.url, suppress_embeds=True)
            else:
                await ctx.send(content=random_result.markdown, suppress_embeds=True)


async def setup(bot: AssistantBot):
    await bot.add_cog(Dictionary(bot))
