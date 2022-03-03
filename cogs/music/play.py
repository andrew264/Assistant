import re
from typing import Optional

import disnake
import lavalink
from disnake.ext import commands
from lavalink import DefaultPlayer as Player

from assistant import Client, VideoTrack, VoiceClient


class SlashPlay(commands.Cog):
    def __init__(self, client: Client):
        self.player: Optional[Player] = None
        self.client = client
        self.lavalink = client.lavalink

    @commands.slash_command(name="play", description="Play Music in VC 🎶", guild_ids=[821758346054467584])
    async def play(self, inter: disnake.ApplicationCommandInteraction,
                   query: str = commands.Param(description="Search or Enter URL", )) -> None:
        player: Player = self.client.lavalink.player_manager.get(inter.guild.id)
        await inter.response.send_message("Adding to queue...", delete_after=10)
        results = await player.node.get_tracks(query)
        for track in results["tracks"]:
            player.add(VideoTrack(data=track, author=inter.author))
        if results['loadType'] == 'PLAYLIST_LOADED':
            await inter.followup.send(content=f"Playlist **{results['playlistInfo']['name']}** added to queue.",
                                      delete_after=30)
        else:
            await inter.followup.send(content=f"Added `{results['tracks'][0]['info']['title']}` to queue.",
                                      delete_after=30)
        # Join VC
        voice = disnake.utils.get(self.client.voice_clients, guild=inter.guild)
        if voice and player.is_connected:
            pass
        elif voice is None:
            await inter.author.voice.channel.connect(cls=VoiceClient)

        # Start playing
        if player.queue and not player.is_playing:
            await player.set_volume(40)
            bands = [
                (0, 0.0), (1, 0.0), (2, 0.0), (3, 0.0), (4, 0.0),
                (5, 0.0), (6, 0.0), (7, 0.0), (8, 0.0), (9, 0.0),
                (10, 0.0), (11, 0.0), (12, 0.0), (13, 0.0), (14, 0.0)
            ]
            flat_eq = lavalink.filters.Equalizer()
            flat_eq.update(bands=bands)
            await player.set_filter(flat_eq)
            await player.play()

    @play.autocomplete('query')
    async def play_autocomplete(self, inter: disnake.ApplicationCommandInteraction, query: str) -> dict:
        if not self.player:
            self.player: Player = self.lavalink.player_manager.create(inter.guild.id)
        if not query or len(query) < 3:
            return {}
        url_rx = re.compile(r'https?://(?:www\.)?.+')
        query = query if url_rx.match(query) else f'ytsearch:{query}'
        results = await self.player.node.get_tracks(query)
        if not results or not results["tracks"]:
            return {}
        elif results['loadType'] == 'PLAYLIST_LOADED':
            return {results['playlistInfo']['name']: query}
        else:
            return {result["info"]["title"]: result["info"]["uri"] for result in results["tracks"][:5]}

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
