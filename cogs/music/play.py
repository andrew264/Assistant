import asyncio
import json
import os
import re
from itertools import islice

import disnake
import lavalink
from disnake.ext import commands
from fuzzywuzzy import process
from lavalink import DefaultPlayer as Player

from assistant import Client, VideoTrack, VoiceClient, remove_brackets
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

    def _search_cache(self, query: str) -> dict:
        result = {"Search: " + query: query}

        for identifier, title in self._cache.items():
            if identifier in query.split('/') or identifier in query.split('='):
                result[title] = "https://www.youtube.com/watch?v=" + identifier

        # search in Titles
        fuzzy_search = process.extractBests(query, self._cache, score_cutoff=85, limit=7)
        keys = [k[-1] for k in fuzzy_search]
        for key in keys:
            result[self._cache[key]] = "https://www.youtube.com/watch?v=" + key

        return dict(islice(result.items(), 10))

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

    @commands.slash_command(description="Play Music in VC 🎶")
    @commands.guild_only()
    async def play(self, inter: disnake.ApplicationCommandInteraction,
                   query: str = commands.Param(description="Search or Enter URL", )) -> None:
        if self.client.lavalink is None:
            await inter.response.send_message("Music Player is not connected.", ephemeral=True)
            return
        if self.player_manager is None:
            await self._connect_to_lavalink()
        player: Player = self.player_manager.create(inter.guild.id)
        await inter.response.defer()

        is_search = False if url_rx.match(query) else True
        query = f'ytsearch:{query}' if is_search else query

        results = await player.node.get_tracks(query)
        for track in results["tracks"]:
            track = VideoTrack(track, author=inter.author)
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
            vol_filter.update(volume=0.4)
            await player.set_filter(vol_filter)
            flat_eq = lavalink.Equalizer()
            flat_eq.update(bands=[(band, 0.0) for band in range(0, 15)])
            await player.set_filter(flat_eq)
            await player.play()
            self.client.logger.info(f"Started playing {player.current.title} in {inter.guild.name}")

    @play.autocomplete('query')
    async def play_autocomplete(self, inter: disnake.ApplicationCommandInteraction, query: str) -> dict:
        if not query or len(query) < 3:
            return {"No Results Found": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
        return self._search_cache(query)

    # Checks
    @play.before_invoke
    async def check_play(self, inter: disnake.ApplicationCommandInteraction) -> None:
        if inter.author.voice is None:
            raise commands.CheckFailure("You are not connected to a voice channel.")

        if inter.guild.voice_client is not None and inter.author.voice is not None:
            if inter.guild.voice_client.channel != inter.author.voice.channel:
                raise commands.CheckFailure("You must be in same VC as Bot.")

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
