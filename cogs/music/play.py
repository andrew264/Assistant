import asyncio
import re
from collections import defaultdict
from typing import Optional, Dict, Any, cast

import discord
import wavelink
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands
from thefuzz import process
from wavelink import Playable, Playlist

from assistant import AssistantBot
from config import HOME_GUILD_ID, LavaConfig
from utils import check_vc, clickable_song, remove_brackets
from utils.tenor import TenorObject

url_rx = re.compile(r'https?://(?:www\.)?.+')


class Play(commands.Cog):
    def __init__(self, bot: AssistantBot):
        self.bot = bot
        self._mongo_client: Optional[Any] = None  # type: ignore
        self._cache: Dict[int, Dict[str, str]] = defaultdict()
        self._tenor = TenorObject()

    @property
    def mongo_client(self) -> Any:  # type: ignore
        if not self._mongo_client:
            self._mongo_client = self.bot.connect_to_mongo()
        return self._mongo_client

    @commands.Cog.listener('on_wavelink_track_start')
    async def _add_track_to_db(self, payload: wavelink.TrackStartEventPayload) -> None:
        assert payload.player.guild is not None
        self.bot.logger.info(f"[LAVALINK] Playing {payload.track.title} on {payload.player.guild}")
        player = payload.player
        guild_id = player.guild.id
        track = player.current
        if track.uri is None:
            return
        title = remove_brackets(track.title)
        if guild_id not in self._cache:
            await self._fill_cache(guild_id)
        self._cache[guild_id] |= {title: track.uri}
        db = self.mongo_client["assistant"]
        collection = db["songHistory"]
        new_song = dict(title=title, uri=track.uri)
        result = await collection.update_one(
            {"_id": guild_id},
            {
                "$push": {
                    "songs": {
                        "$each": [new_song],
                        "$slice": -100
                    }
                },
            }
        )
        if result.modified_count:
            self.bot.logger.debug(f"[MONGO] Added {title} to songHistory collection for GuildID: {guild_id}")
        else:
            self.bot.logger.debug(f"[MONGO] {title} already exists in GuildID: {guild_id}")

    async def _fill_cache(self, guild_id: int):
        db = self.mongo_client["assistant"]
        collection = db["songHistory"]
        self._cache[guild_id] = {}
        if await collection.count_documents({"_id": guild_id}) == 0:
            self.bot.logger.debug(f"[MONGO] Creating new document for GuildID: {guild_id} in songHistory collection")
            await collection.insert_one({"_id": guild_id, "songs": []})
            await asyncio.sleep(1)  # wait for mongo to create the document
            return
        history = await collection.find_one({"_id": guild_id})
        for song in history['songs']:
            self._cache[guild_id] |= {song['title']: song['uri']}
        self.bot.logger.debug(f"[MONGO] Filled cache for GuildID: {guild_id} with {len(self._cache[guild_id])} songs")

    @commands.hybrid_command(name="play", aliases=["p"], description="Play a song")
    @app_commands.describe(query="Title/URL of the song to play")
    @commands.guild_only()
    @check_vc()
    async def play(self, ctx: commands.Context, *, query: Optional[str] = None):
        assert isinstance(ctx.author, discord.Member)

        if not ctx.voice_client:
            await ctx.author.voice.channel.connect(cls=wavelink.Player, self_deaf=True)
        vc: wavelink.Player = cast(wavelink.Player, ctx.voice_client)
        vc.autoplay = wavelink.AutoPlayMode.disabled

        if not query:
            if vc.current is None and vc.queue.is_empty:
                message = "I am not playing anything right now."
            elif vc.paused:
                await vc.pause(False)
                message = f"Resuming: {clickable_song(vc.current)}"
            else:
                await vc.pause(True)
                message = f"Paused: {clickable_song(vc.current)}"

            await ctx.send(message, suppress_embeds=True)
            return

        await ctx.defer()
        if not re.match(url_rx, query):
            query = f"ytsearch:{query}"

        try:
            tracks = await wavelink.Pool.fetch_tracks(query)
        except wavelink.LavalinkLoadException as e:
            await ctx.send(f"Something went wrong!\n{e.error}")
            raise commands.CommandError(f"Something went wrong while fetching the song: {e}")
        if isinstance(tracks, list):
            if not tracks:
                await ctx.send("No results found")
                return
            track: Playable = tracks[0]
            await ctx.send(f"Added {clickable_song(track)} to queue", suppress_embeds=True,)

            if ctx.guild.id == HOME_GUILD_ID:
                if vc.current is None: delete_after = int(track.length / 1000)
                else: delete_after = 900  # 15 minutes
                a_gif = await self._tenor.search_async(track.author + " " + track.title)
                if a_gif: await ctx.channel.send(a_gif, delete_after=delete_after)

            await vc.queue.put_wait(track)
        elif isinstance(tracks, Playlist):
            await vc.queue.put_wait(tracks)
            await ctx.send(f"Added {len(tracks)} songs to queue")
        else:
            await ctx.send("Something went wrong")
            self.bot.logger.error(f"[LAVALINK] Something went wrong while fetching {query}")

        if not vc.playing:
            vc.filters.volume = 0.3
            await vc.play(track=vc.queue.get())
            return

    @play.autocomplete('query')
    async def play_autocomplete(self, ctx: discord.Interaction, query: str) -> list[Choice[str]]:
        assert ctx.guild is not None
        guild_id = ctx.guild.id
        if guild_id not in self._cache:
            await self._fill_cache(guild_id)
        if query == "":
            return [Choice(name="Enter a song name or URL", value="https://youtu.be/dQw4w9WgXcQ")]

        result = {"Search: " + query: query} if query else {}

        cache_data = self._cache[guild_id]
        title_matches = process.extractBests(query, [title for title, _ in cache_data.items()], limit=24,
                                             score_cutoff=80)
        url_matches = process.extractBests(query, [url for _, url in cache_data.items()], limit=24, score_cutoff=70)

        combined_matches = sorted(title_matches + url_matches, key=lambda x: x[1], reverse=True)
        for title_or_url, score in combined_matches[:24]:
            if title_or_url in cache_data:  # Title match
                result[title_or_url] = cache_data[title_or_url]
            elif title_or_url in cache_data.values():  # URL match
                title = next(title for title, url in cache_data.items() if url == title_or_url)
                if title not in result:
                    result[title] = title_or_url
            else:
                self.bot.logger.error(f"[LAVALINK] Something went wrong while fetching {query}")
        return [Choice(name=k, value=v) for k, v in result.items()]


async def setup(bot: AssistantBot):
    lc = LavaConfig()
    if not lc:
        return
    await bot.add_cog(Play(bot))
