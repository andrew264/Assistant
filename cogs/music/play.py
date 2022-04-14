import asyncio
import re
from typing import Optional

import disnake
import lavalink
from disnake.ext import commands
from lavalink import DefaultPlayer as Player

from assistant import Client, VideoTrack, VoiceClient

url_rx = re.compile(r'https?://(?:www\.)?.+')
no_results = {"No Results Found": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}


class SlashPlay(commands.Cog):
    def __init__(self, client: Client):
        self.player: Optional[Player] = None
        self.client = client
        self.lavalink = client.lavalink

    @commands.slash_command(description="Play Music in VC 🎶")
    @commands.guild_only()
    async def play(self, inter: disnake.ApplicationCommandInteraction,
                   query: str = commands.Param(description="Search or Enter URL", )) -> None:
        player: Player = self.client.lavalink.player_manager.get(inter.guild.id)
        await inter.response.defer()

        # search again it query is not url
        is_search = False if url_rx.match(query) else True
        query = f'ytsearch:{query}' if is_search else query

        results = await player.node.get_tracks(query)
        for track in results["tracks"]:
            player.add(VideoTrack(data=track, author=inter.author))
            if is_search:  # if is_search, only add the first track
                break
        if results['loadType'] == 'PLAYLIST_LOADED':
            await inter.edit_original_message(content=f"Playlist **{results['playlistInfo']['name']}** added to queue.")
            self.client.logger.info(
                f"{inter.author.display_name} added playlist {results['playlistInfo']['name']} to queue.")
        else:
            await inter.edit_original_message(content=f"Added `{results['tracks'][0]['info']['title']}` to queue.", )
            self.client.logger.info(
                f"{inter.author.display_name} added {results['tracks'][0]['info']['title']} to queue.")
        await inter.delete_original_message(delay=30)
        # Join VC
        voice = disnake.utils.get(self.client.voice_clients, guild=inter.guild)
        if voice is None:
            await inter.author.voice.channel.connect(cls=VoiceClient)
            self.client.logger.info(f"Connected to {inter.author.voice.channel}")
            if isinstance(inter.author.voice.channel, disnake.StageChannel):
                if inter.author.voice.channel.permissions_for(inter.guild.me).stage_moderator:
                    await asyncio.sleep(0.5)
                    await inter.guild.me.request_to_speak()
                    self.client.logger.info(f"Requesting to speak.")

        # Start playing
        if player.queue and not player.is_playing:
            await player.clear_filters()
            vol_filter = lavalink.Volume()
            vol_filter.update(volume=0.4)
            await player.set_filter(vol_filter)
            flat_eq = lavalink.Equalizer()
            flat_eq.update(bands=[(band, 0.0) for band in range(0, 15)])
            await player.set_filter(flat_eq)
            await player.play()
            self.client.logger.info(f"Started playing {player.current.title}")

    @play.autocomplete('query')
    async def play_autocomplete(self, inter: disnake.ApplicationCommandInteraction, query: str) -> dict:
        if not query or len(query) < 3:
            return no_results
        if self.player is None:
            self.player: Player = self.lavalink.player_manager.create(inter.guild.id)
        query = query if url_rx.match(query) else f'ytsearch:{query}'
        results = await self.player.node.get_tracks(query)
        if not results or not results["tracks"]:
            return no_results
        elif results['loadType'] == 'PLAYLIST_LOADED':
            return {results['playlistInfo']['name']: query}
        else:
            return {result["info"]["title"]: result["info"]["uri"] for result in results["tracks"][:7]}

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
    client.add_cog(SlashPlay(client))
