import re

import disnake
import lavalink
from disnake.ext import commands
from lavalink import DefaultPlayer as Player

from assistant import VideoTrack, VoiceClient, Client


class Play(commands.Cog):
    def __init__(self, client: Client):
        self.client = client
        self.lavalink = client.lavalink

    # Play
    @commands.command(pass_context=True, aliases=["p"])
    @commands.guild_only()
    async def old_play(self, ctx: commands.Context, *, query: str = None) -> None:

        player: Player = self.lavalink.player_manager.create(ctx.guild.id)
        await ctx.message.delete(delay=5)
        # If player is paused, resume player
        if query is None:
            if player.current and player.paused:
                if ctx.voice_client is None:
                    return
                await player.set_pause(pause=False)
                await ctx.send(f"Resumed {player.current.title}", delete_after=10)
                return
            else:
                await player.set_pause(pause=True)
                await ctx.send("Paused", delete_after=10)
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
            for track in results["tracks"]:
                player.add(VideoTrack(data=track, author=ctx.author))
            if results['loadType'] == 'PLAYLIST_LOADED':
                await ctx.send(f"{len(results['tracks'])} tracks added from {results['playlistInfo']['name']}",
                               delete_after=20)
            else:
                await ctx.send(f"Adding `{results['tracks'][0]['info']['title']}` to Queue.", delete_after=20)
                yt_time_rx = re.compile(r"^(https?\:\/\/)?(www\.)?(youtube\.com|youtu\.?be)\/.+(t=|start=)")
                if yt_time_rx.match(query):
                    seek_time = int(re.sub(yt_time_rx, "", query)) * 1000

        # Join VC
        voice = disnake.utils.get(self.client.voice_clients, guild=ctx.guild)
        if voice and player.is_connected:
            pass
        elif voice is None:
            await ctx.author.voice.channel.connect(cls=VoiceClient)

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
    @old_play.before_invoke
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
