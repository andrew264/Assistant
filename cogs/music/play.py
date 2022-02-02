import re

import disnake
import lavalink
from disnake.ext import commands
from disnake.utils import get
from lavalink import DefaultPlayer as Player

from cogs.music.lavaclient import LavalinkVoiceClient
from cogs.music.lavatrack import VideoTrack


class Play(commands.Cog):
    def __init__(self, client: disnake.Client):
        self.client = client
        if not hasattr(client, 'lavalink'):
            client.lavalink = lavalink.Client(client.user.id)
            client.lavalink.add_node('192.168.1.36', 2333, 'youshallnotpass', 'in', 'assistant-node')

    # Play
    @commands.command(pass_context=True, aliases=["p"])
    @commands.guild_only()
    async def play(self, ctx: commands.Context, *, query: str = None) -> None:

        player: Player = self.client.lavalink.player_manager.create(ctx.guild.id, endpoint=str(ctx.guild.region))
        await ctx.message.delete(delay=5)
        # If player is paused, resume player
        if query is None:
            if player.current and player.paused:
                if ctx.voice_client is None:
                    return
                await player.set_pause(pause=False)
                return
            else:
                await ctx.send("Nothing to Play", delete_after=10)
                return

        async with ctx.typing():
            url_rx = re.compile(r'https?://(?:www\.)?.+')
            if not url_rx.match(query):
                query = f'ytsearch:{query}'
            results = await player.node.get_tracks(query)
            seek_time = 0
            if not results or not results['tracks']:
                await ctx.send("Nothing to Play", delete_after=10)
                return
            if results['loadType'] == 'PLAYLIST_LOADED':
                tracks = results['tracks']
                for track in tracks:
                    track = VideoTrack(data=track, author=ctx.author)
                    player.add(requester=ctx.author.id, track=track)
                await ctx.send(f"{len(tracks)} tracks added from {results['playlistInfo']['name']}", delete_after=20)
            else:
                track = VideoTrack(data=results['tracks'][0], author=ctx.author)
                player.add(requester=ctx.author.id, track=track)
                await ctx.send(f"Adding `{results['tracks'][0]['info']['title']}` to Queue.", delete_after=20)
                yt_time_rx = re.compile(r"^(https?\:\/\/)?(www\.)?(youtube\.com|youtu\.?be)\/.+(t=|start=)")
                if yt_time_rx.match(query):
                    seek_time = int(re.sub(yt_time_rx, "", query)) * 1000

        # Join VC
        voice = get(self.client.voice_clients, guild=ctx.guild)
        if voice and player.is_connected:
            pass
        elif voice is None:
            await ctx.author.voice.channel.connect(cls=LavalinkVoiceClient)

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
            if seek_time:
                await player.seek(seek_time)

    # Play Checks
    @play.before_invoke
    async def check_play(self, ctx: commands.Context) -> None:
        if ctx.author.voice is None:
            raise commands.CheckFailure("You are not connected to a voice channel.")
        if ctx.voice_client is not None and ctx.author.voice is not None:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                raise commands.CheckFailure("You must be in same VC as Bot.")
        permissions = ctx.author.voice.channel.permissions_for(ctx.me)
        if not permissions.connect or not permissions.speak:
            raise commands.CheckFailure('Missing `CONNECT` and `SPEAK` permissions.')


def setup(client):
    client.add_cog(Play(client))
