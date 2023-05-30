import asyncio
import json
import os
import re
from itertools import islice
from typing import Any

import disnake
import lavalink
from disnake.ext import commands
from fuzzywuzzy import process
from lavalink import DefaultPlayer as Player

from assistant import Client, VoiceClient, remove_brackets
from assistant.track import TrackInfo
from config import LavalinkConfig

url_rx = re.compile(r'https?://(?:www\.)?.+')


class SlashPlay(commands.Cog):
    def __init__(self, client: Client):
        self.client = client
        self._cache = {}
        with open("data/search_cache.json", "r") as f:
            self._cache = json.load(f)
            f.close()
        del f
        self.player_manager = None
        self.mongo_client: Any = None

    def _search_cache(self, query: str) -> dict:
        result = {"Search: " + query: query}

        for identifier, title in self._cache.items():
            if identifier in query.split('/') or identifier in query.split('='):
                result[title] = "https://www.youtube.com/watch?v=" + identifier

        # search in Titles
        fuzzy_search = process.extractBests(query, self._cache, score_cutoff=85, limit=7)
        keys = [k[-1] for k in fuzzy_search]
        for key in keys:
            assert isinstance(key, str)
            result[self._cache[key]] = "https://www.youtube.com/watch?v=" + key

        return dict(islice(result.items(), 10))

    async def _search_history(self, guild_id: int, query: str) -> dict:
        assert self.mongo_client is not None
        collection = self.mongo_client["assistant"]["songHistory"]
        result = {"Search: " + query: query} if query else {}
        song_history = await collection.find_one(dict(_id=guild_id))
        if song_history is None:
            return result
        
        songs = song_history["songs"]
        for song in songs:
            result[f"{song['title']} by {song['by']}"] = song["uri"]
        return result

    def _update_cache(self) -> None:
        with open("data/search_cache.json", "w") as f:
            json.dump(self._cache, f, indent=4)
            f.close()
        del f
        return

    @commands.Cog.listener('on_ready')
    async def _connect_to_lavalink(self) -> None:
        config = LavalinkConfig()
        if config and self.client.lavalink is None:
            self.client.lavalink = lavalink.Client(self.client.user.id)
            self.client.logger.info("Connecting to Lavalink...")
            self.player_manager = self.client.lavalink.player_manager
            self.client.lavalink.add_node(host=config.host, port=config.port, password=config.password,
                                          region=config.region, name=config.node_name)
            self.client.logger.info("Connected to Lavalink")
            del config
            self.client.add_listener(self.client.lavalink.voice_update_handler, "on_socket_response")

    @commands.Cog.listener('on_ready')
    async def _connect_to_mongo(self) -> None:
        if self.mongo_client is None:
            self.mongo_client = self.client.connect_to_mongo()

    @commands.slash_command(description="Play Music in VC 🎶")
    @commands.guild_only()
    async def play(self, inter: disnake.ApplicationCommandInteraction,
                   query: str = commands.Param(description="Search or Enter URL", )) -> None:
        if self.client.lavalink is None:
            await inter.response.send_message("Music Player is not connected.", ephemeral=True)
            return
        if self.player_manager is None:
            await self._connect_to_lavalink()
        
        assert isinstance(inter.author, disnake.Member)
        assert isinstance(inter.guild, disnake.Guild)
        assert isinstance(inter.author.voice, disnake.VoiceState)
        player: Player = self.player_manager.create(inter.guild.id) # type: ignore
        await inter.response.defer()

        is_search = False if url_rx.match(query) else True
        query = f'ytsearch:{query}' if is_search else query

        results = await player.node.get_tracks(query)
        for track in results["tracks"]:
            track.extra = dict(info=TrackInfo(author=inter.author, data=track,))
            player.add(track)
            self._cache[track.identifier] = remove_brackets(track.title)

            if is_search:  # if is_search, only add the first track
                break

        if results['loadType'] == 'PLAYLIST_LOADED':
            title = "[PLAYLIST] " + results['playlistInfo']['name']
        elif results['loadType'] == 'SEARCH_RESULT' or results['loadType'] == 'TRACK_LOADED':
            title = results['tracks'][0]['info']['title']
        else:
            await inter.edit_original_message(content="No results found.")
            return

        await inter.edit_original_message(content=f"Added `{title}` to the queue")
        self.client.logger.info(f"{inter.author} added {title} to the queue in {inter.guild.name}")

        # Join VC
        voice = disnake.utils.get(self.client.voice_clients, guild=inter.guild)
        if voice is None:
            assert isinstance(inter.author.voice.channel, disnake.VoiceChannel)
            await inter.author.voice.channel.connect(cls=VoiceClient)
            self.client.logger.info(f"Connected to #{inter.author.voice.channel} in {inter.guild.name}")
            if isinstance(inter.author.voice.channel, disnake.StageChannel):
                await asyncio.sleep(1)
                if inter.guild.me.voice:
                    await inter.guild.me.request_to_speak()
                    self.client.logger.info(
                        f"Requesting to speak in #{inter.guild.me.voice.channel} {inter.guild.name}.")

        # Start playing
        self._update_cache()
        if player.queue and not player.is_playing:
            await player.clear_filters()
            vol_filter = lavalink.Volume()
            vol_filter.update(volume=1.0)
            await player.set_filter(vol_filter)
            flat_eq = lavalink.Equalizer()
            flat_eq.update(bands=[(band, 0.0) for band in range(0, 15)])
            await player.set_filter(flat_eq)
            await player.play()
            assert player.current is not None
            self.client.logger.info(f"Started playing {player.current.title} in {inter.guild.name}")

    @play.autocomplete('query')
    async def play_autocomplete(self, inter: disnake.ApplicationCommandInteraction, query: str) -> dict:
        assert inter.guild is not None
        if not query or len(query) < 4:
            return await self._search_history(guild_id=inter.guild.id, query=query)
        return self._search_cache(query)

    # Checks
    @play.before_invoke
    async def check_play(self, inter: disnake.ApplicationCommandInteraction) -> None:
        assert isinstance(inter.author, disnake.Member)
        assert isinstance(inter.guild, disnake.Guild)
        assert isinstance(inter.me, disnake.Member)
        
        if inter.author.voice is None:
            raise commands.CheckFailure("You are not connected to a voice channel.")

        if inter.guild.voice_client is not None and inter.author.voice is not None:
            if inter.guild.voice_client.channel != inter.author.voice.channel:
                raise commands.CheckFailure("You must be in same VC as Bot.")
            
        assert isinstance(inter.author.voice.channel, disnake.VoiceChannel)
        permissions = inter.author.voice.channel.permissions_for(inter.me)
        if not permissions.connect or not permissions.speak:
            raise commands.CheckFailure('Missing `CONNECT` and `SPEAK` permissions.')


def setup(client: Client):
    config = LavalinkConfig()
    if not config:
        client.logger.warning("Lavalink Config not found. Music Player will not be loaded.")
        return
    # check if cache exists
    if not os.path.exists("data/search_cache.json"):
        client.logger.info("Music Search Cache not found, creating one...")
        with open("data/search_cache.json", "w") as f:
            json.dump({}, f)
            f.close()
        del f
    client.add_cog(SlashPlay(client))
