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
from wavelink import Playlist

from assistant import AssistantBot
from config import LavaConfig, HOME_GUILD_ID, STATUS, ACTIVITY_TYPE, ACTIVITY_TEXT
from utils import check_vc, remove_brackets, clickable_song

url_rx = re.compile(r'https?://(?:www\.)?.+')


class Play(commands.Cog):
    def __init__(self, bot: AssistantBot):
        self.bot = bot
        self._mongo_client: Optional[Any] = None  # type: ignore
        self._cache: Dict[int, Dict[str, str]] = defaultdict()

    @property
    def mongo_client(self) -> Any:  # type: ignore
        if not self._mongo_client:
            self._mongo_client = self.bot.connect_to_mongo()
        return self._mongo_client

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node) -> None:
        self.bot.logger.info(f"[LAVALINK] Node {node.identifier} is ready.")

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload) -> None:
        assert payload.player.guild is not None
        self.bot.logger.info(f"[LAVALINK] Playing {payload.track.title} on {payload.player.guild}")
        await self._add_track_to_db(payload.player)
        await self.reset_dc(payload.player)
        if payload.player.guild.id == HOME_GUILD_ID:
            await self.bot.change_presence(status=STATUS,
                                           activity=discord.Activity(type=discord.ActivityType.listening,
                                                                     name=remove_brackets(payload.track.title)))

    async def schedule_dc(self, player: wavelink.Player, delay: int = 300):
        await asyncio.sleep(delay)
        if not player.playing and not player.queue:
            await player.set_filters(None)
            await player.disconnect(force=True)
            self.bot.logger.info(f"[LAVALINK] Disconnected from {player.guild}")

    async def reset_dc(self, player: wavelink.Player):
        if hasattr(player, "dc_task"):
            player.dc_task.cancel()
        player.dc_task = self.bot.loop.create_task(self.schedule_dc(player))

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload) -> None:
        assert payload.player.guild is not None
        self.bot.logger.info(f"[LAVALINK] Finished playing {payload.track.title} on {payload.player.guild}")
        if payload.player.queue or payload.player.queue.mode.loop or payload.player.queue.mode.loop_all:
            await payload.player.play(payload.player.queue.get())
            await asyncio.sleep(1)
        if not payload.player.current:
            await self.schedule_dc(payload.player)
            if payload.player.guild.id == HOME_GUILD_ID:
                await self.bot.change_presence(status=STATUS,
                                               activity=discord.Activity(type=ACTIVITY_TYPE, name=ACTIVITY_TEXT), )

    async def _fill_cache(self, guild_id: int):
        db = self.mongo_client["assistant"]
        collection = db["songHistory"]
        history = await collection.find_one({"_id": guild_id})
        self._cache[guild_id] = {}
        for song in history['songs']:
            self._cache[guild_id] |= {song['title']: song['uri']}
        self.bot.logger.info(f"[MONGO] Filled cache for {guild_id} with {len(self._cache[guild_id])} songs")

    async def _add_track_to_db(self, player: wavelink.Player):
        assert player.guild is not None
        assert player.current is not None
        guild_id = player.guild.id
        track = player.current
        if track.uri is None:
            return
        title = track.title
        if not self._cache[guild_id]:
            await self._fill_cache(guild_id)
        self._cache[guild_id] |= {title: track.uri}
        db = self.mongo_client["assistant"]
        collection = db["songHistory"]
        await collection.update_one(
            {"_id": guild_id},
            {"$addToSet": {"songs": dict(title=title, uri=track.uri)}},
            upsert=True
        )
        self.bot.logger.info(f"[MONGO] Added {title} to {guild_id}")

    @commands.hybrid_command(name="play", aliases=["p"], description="Play a song")
    @app_commands.describe(query="Title/URL of the song to play")
    @commands.guild_only()
    @check_vc()
    async def play(self, ctx: commands.Context, *, query: Optional[str] = None):
        assert isinstance(ctx.author, discord.Member)

        vc: wavelink.Player
        vc = cast(wavelink.Player, ctx.voice_client)

        if not ctx.voice_client:
            vc: wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player,  # type: ignore
                                                                         self_deaf=True)

        vc.autoplay = wavelink.AutoPlayMode.disabled

        if not query:
            if not (vc.current or vc.queue):
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
        except wavelink.LavalinkLoadException:
            await ctx.send("Invalid URL")
            return
        if isinstance(tracks, list):
            track = tracks[0]
            await vc.queue.put_wait(track)
            await ctx.send(f"Added {clickable_song(track)} to queue", suppress_embeds=True)
        elif isinstance(tracks, Playlist):
            await vc.queue.put_wait(tracks)
            await ctx.send(f"Added {len(tracks)} songs to queue")
        else:
            await ctx.send("Something went wrong")
            self.bot.logger.error(f"[LAVALINK] Something went wrong while fetching {query}")

        if not vc.playing:
            await vc.play(track=vc.queue.get())
            await vc.set_volume(30)

    @play.autocomplete('query')
    async def play_autocomplete(self, ctx: discord.Interaction, query: str) -> list[Choice[str]]:
        assert ctx.guild is not None
        if query == "":
            return [Choice(name="Enter a song name or URL", value="https://youtu.be/dQw4w9WgXcQ")]
        result = {"Search: " + query: query} if query else {}
        guild_id = ctx.guild.id
        if guild_id not in self._cache:
            await self._fill_cache(guild_id)
        split_term = ' <URL> '
        _cache = [f"{title}{split_term}{url}" for title, url in self._cache[guild_id].items()]
        search = [s[0].split(split_term)[0] for s in process.extractBests(query, _cache, limit=24, score_cutoff=50)]
        for s in search:
            result |= {s: self._cache[guild_id][s]}

        return [Choice(name=k, value=v) for k, v in result.items()]


async def setup(bot: AssistantBot):
    lc = LavaConfig()
    if not lc:
        return
    await bot.add_cog(Play(bot))
