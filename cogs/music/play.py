import json
import re
from typing import List

import disnake
import lavalink
from disnake.ext import commands
from disnake.utils import get
from pyyoutube import Api, PlaylistItem

from EnvVariables import YT_TOKEN

api = Api(api_key=YT_TOKEN)
from cogs.music.lavaclient import LavalinkVoiceClient, VideoTrack


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

        player: lavalink.DefaultPlayer = self.client.lavalink.player_manager.create(ctx.guild.id,
                                                                                    endpoint=str(ctx.guild.region))

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
            playlist_rx = re.compile(r"^(https?\:\/\/)?(www\.)?(youtube\.com)\/(playlist).+$", re.IGNORECASE)
            if re.match(playlist_rx, query) is not None:
                playlist = True
                playlist_id = query.replace("https://www.youtube.com/playlist?list=", "")
                video_items: List[PlaylistItem] = api.get_playlist_items(playlist_id=playlist_id, count=None).items
                video_ids = [video.snippet.resourceId.videoId for video in video_items]
                await ctx.send(f"Adding Playlist to Queue...", delete_after=20)
            else:
                playlist = False
                url_rx = re.compile(r'https?://(?:www\.)?.+')
                if not url_rx.match(query):
                    query = f'ytsearch:{query}'
                result = (await player.node.get_tracks(query))['tracks'][0]
                video_ids = [result['info']['identifier']]
                await ctx.send(f"Adding `{result['info']['title']}` to Queue.", delete_after=20)
            with open("data/MusicCache.json", "r+") as jsonFile:
                data: dict = json.load(jsonFile)
                for video_id in video_ids:
                    if playlist:
                        result = (await player.node.get_tracks(video_id))['tracks'][0]
                    if video_id in data:
                        track = VideoTrack(data=result, author=ctx.author, video_dict=data[video_id])
                    else:
                        track = VideoTrack(data=result, author=ctx.author)
                        data.update(track.toDict())
                    player.add(requester=ctx.author.id, track=track)
                jsonFile.seek(0)
                json.dump(data, jsonFile, indent=4, sort_keys=True)
                jsonFile.close()

        # Join VC
        voice = get(self.client.voice_clients, guild=ctx.guild)
        if voice and player.is_connected:
            pass
        elif voice is None:
            player.store('channel', ctx.channel.id)
            await ctx.author.voice.channel.connect(cls=LavalinkVoiceClient)

        if player.queue and not player.is_playing:
            await player.set_volume(40)
            await player.play()

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
