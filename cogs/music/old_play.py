import asyncio
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
    @commands.command(pass_context=True, aliases=["p", "play"])
    @commands.guild_only()
    async def old_play(self, ctx: commands.Context, *, query: str = None) -> None:

        player: Player = self.lavalink.player_manager.create(ctx.guild.id)
        await ctx.message.delete(delay=5)
        # If player is paused, resume player
        if query is None:
            if ctx.voice_client is None:
                return
            if player.current:
                if player.paused:
                    await player.set_pause(pause=False)
                    await ctx.send(f"Resumed {player.current.title}", delete_after=10)
                    return
                else:
                    await player.set_pause(pause=True)
                    await ctx.send("Paused", delete_after=10)
                    return
            else:
                await ctx.send("Nothing to Play", delete_after=10)
                return

        async with ctx.typing():

            url_rx = re.compile(r'https?://(?:www\.)?.+')
            is_search = False if url_rx.match(query) else True
            query = f'ytsearch:{query}' if is_search else query

            results = await player.node.get_tracks(query)
            if not results or not results['tracks']:
                await ctx.send("No Results Found.", delete_after=10)
                return
            for track in results["tracks"]:
                player.add(track=VideoTrack(data=track, author=ctx.author))
                if is_search:  # If is_search, only add first result
                    break
            if results['loadType'] == 'PLAYLIST_LOADED':
                await ctx.send(f"{len(results['tracks'])} tracks added from {results['playlistInfo']['name']}",
                               delete_after=20)
            else:
                await ctx.send(f"Adding `{results['tracks'][0]['info']['title']}` to Queue.", delete_after=20)
                yt_time_rx = re.compile(r"^(https?\:\/\/)?(www\.)?(youtube\.com|youtu\.?be)\/.+(t=|start=)")

        seek_time = int(re.sub(yt_time_rx, "", query)) * 1000 if yt_time_rx.match(query) else 0

        # Join VC
        voice = disnake.utils.get(self.client.voice_clients, guild=ctx.guild)
        if voice is None:
            await ctx.author.voice.channel.connect(cls=VoiceClient)
            if isinstance(ctx.author.voice.channel, disnake.StageChannel):
                if ctx.author.voice.channel.permissions_for(ctx.me).stage_moderator:
                    await asyncio.sleep(0.5)
                    await ctx.me.request_to_speak()

        if player.queue and not player.is_playing:
            for _filter in list(player.filters):
                await player.remove_filter(_filter)
            vol_filter = lavalink.filters.Volume()
            vol_filter.update(volume=0.4)
            await player.set_filter(vol_filter)
            flat_eq = lavalink.Equalizer()
            flat_eq.update(bands=[(band, 0.0) for band in range(0, 15)])
            await player.set_filter(flat_eq)
            await player.play()

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
