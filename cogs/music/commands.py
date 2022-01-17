# Imports
import asyncio

import lavalink
from disnake import (
    Activity,
    ActivityType,
    Client,
    Embed,
    FFmpegPCMAudio,
    PCMVolumeTransformer,
    Status,
    VoiceClient,
    NotFound,
)
from disnake.ext import commands
from disnake.utils import get
from lavalink import AudioTrack

from cogs.music.fetch import (
    FindInputType,
    InputType,
    FetchVideo,
    Search,
    FetchPlaylist,
    StreamURL,
    vid_id_regex,
)
from cogs.music.lavaclient import LavalinkVoiceClient
from cogs.music.loop import LoopType
from cogs.music.misc import AddTagstoJSON
from cogs.music.nowplaying import NowPlayingButtons
from cogs.music.queue import QueuePages, QueueEmbed
from cogs.music.videoinfo import VideoInfo

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -multiple_requests 1",
    "options": "-vn",
}


class Music(commands.Cog):
    def __init__(self, client: Client):
        self.client = client
        self.song_queue: dict = {}
        self.queue_props: dict = {}

        if not hasattr(client, 'lavalink'):  # This ensures the client isn't overwritten during cog reloads.
            self.client.lavalink = lavalink.Client(822454735310684230)
            self.client.lavalink.add_node('127.0.0.1', 2333, 'youshallnotpass', 'in', 'assistant-node')

    # Play
    @commands.command(pass_context=True, aliases=["p"])
    @commands.guild_only()
    async def play(self, ctx: commands.Context, *, query: str = None) -> None:

        player = self.client.lavalink.player_manager.create(ctx.guild.id, endpoint=str(ctx.guild.region))

        # create Dictionary
        if ctx.guild.id not in self.song_queue:
            self.song_queue[ctx.guild.id] = []
            self.queue_props[ctx.guild.id] = {
                "volume": 25,
                "loop": LoopType.Disabled
            }

        # If player is_paused resume...
        if query is None:
            if self.song_queue[ctx.guild.id] and player.paused:
                if ctx.voice_client is None:
                    return
                await self.pause(ctx)
                return
            else:
                await ctx.send("Nothing to Play")
                return

        async with ctx.typing():
            input_type = FindInputType(query)
            loop = asyncio.get_event_loop()
            match input_type:
                case InputType.Playlist:
                    video_info = await loop.run_in_executor(None, FetchPlaylist, query, ctx.author)
                    self.song_queue[ctx.guild.id].extend(video_info)
                case InputType.Search:
                    video_info = await loop.run_in_executor(None, Search, query, ctx.author)
                    self.song_queue[ctx.guild.id].append(video_info)
                case InputType.URL:
                    video_info = await loop.run_in_executor(None, FetchVideo, query, ctx.author)
                    self.song_queue[ctx.guild.id].append(video_info)

        if input_type == InputType.Playlist:
            await ctx.send(f"Adding Playlist to Queue...")
        else:
            await ctx.send(f"Adding `{self.song_queue[ctx.guild.id][-1].Title}` to Queue.")

        # Join VC
        voice = get(self.client.voice_clients, guild=ctx.guild)
        if voice and player.is_connected:
            pass
        elif voice is None:
            player.store('channel', ctx.channel.id)
            await ctx.author.voice.channel.connect(cls=LavalinkVoiceClient)

        if self.song_queue[ctx.guild.id][0] and not player.is_playing:
            await self.player(ctx)

    # Queue
    @commands.command(aliases=["q"])
    @commands.guild_only()
    async def queue(self, ctx: commands.Context) -> None:
        view = QueuePages(self.song_queue[ctx.guild.id])
        view.message = await ctx.send(embed=QueueEmbed(self.song_queue[ctx.guild.id], 1), view=view)

    # Play from Queue
    async def player(self, ctx: commands.Context) -> None:
        await self.StatusUpdate(ctx)
        if not self.song_queue[ctx.guild.id]:
            return
        current_song: VideoInfo = self.song_queue[ctx.guild.id][0]
        # voice
        player = self.client.lavalink.player_manager.get(ctx.guild.id)
        result = (await player.node.get_tracks(current_song.pURL))['tracks'][0]
        track = AudioTrack(result, current_song.Author.id)
        player.add(requester=current_song.Author.id, track=track)
        await player.set_volume(self.queue_props[ctx.guild.id]["volume"])
        if not player.is_playing:
            await player.play()
        # embed
        embed = Embed(title="", color=0xFF0000)
        embed.set_author(name=f"Playing: {current_song.Title}", url=current_song.pURL, icon_url="")
        embed.set_footer(text=f"Requested by {current_song.Author.display_name}",
                         icon_url=current_song.Author.display_avatar.url)
        await ctx.send(embed=embed, delete_after=current_song.Duration)
        # countdown
        while True:
            if self.song_queue[ctx.guild.id] and self.song_queue[ctx.guild.id][0].SongIn > 0:
                self.song_queue[ctx.guild.id][0].SongIn -= 1
            else:
                await player.stop()
                break  # song ends here
            await asyncio.sleep(1)

        l_type = self.queue_props[ctx.guild.id]["loop"]
        try:
            assert self.song_queue[ctx.guild.id]
        except AssertionError:
            return
        match l_type:
            case LoopType.All:
                self.song_queue[ctx.guild.id][0].SongIn = self.song_queue[ctx.guild.id][0].Duration  # Temp Fix
                self.song_queue[ctx.guild.id].append(self.song_queue[ctx.guild.id][0])
                self.song_queue[ctx.guild.id].pop(0)

            case LoopType.One:
                self.song_queue[ctx.guild.id][0].SongIn = self.song_queue[ctx.guild.id][0].Duration

            case LoopType.Disabled:
                self.song_queue[ctx.guild.id].pop(0)

        await self.player(ctx)

    # Update client's status
    # Cuz why not ?
    async def StatusUpdate(self, ctx: commands.Context) -> None:
        if self.song_queue[ctx.guild.id]:
            await self.client.change_presence(
                activity=Activity(type=ActivityType.listening, name=self.song_queue[ctx.guild.id][0].Title, ))
        else:
            await self.client.change_presence(status=Status.online,
                                              activity=Activity(type=ActivityType.watching, name="yall Homies."), )

    # Skip
    @commands.command()
    @commands.guild_only()
    async def skip(self, ctx: commands.Context, arg: int = 0) -> None:
        player = self.client.lavalink.player_manager.get(ctx.guild.id)
        if not self.song_queue[ctx.guild.id] or arg > len(self.song_queue[ctx.guild.id]):
            return
        await ctx.send(f"{ctx.author.display_name} removed `{self.song_queue[ctx.guild.id][arg].Title}` from Queue.")
        if 0 < arg <= len(self.song_queue[ctx.guild.id]):
            self.song_queue[ctx.guild.id].pop(arg)
        elif arg == 0:
            await player.stop()
            self.song_queue[ctx.guild.id][0].SongIn = 0
            await asyncio.sleep(1)

    # Stop
    @commands.command(aliases=["dc", "kelambu"])
    @commands.guild_only()
    async def stop(self, ctx: commands.Context) -> None:
        player = self.client.lavalink.player_manager.get(ctx.guild.id)
        if player.is_playing or player.paused:
            # Clear the queue to ensure old tracks don't start playing
            # when someone else queues something.
            player.queue.clear()
            # Stop the current track so Lavalink consumes less resources.
            await player.stop()
            # Disconnect from the voice channel.
            await ctx.voice_client.disconnect(force=True)
        # clean list
        if self.song_queue and self.song_queue[ctx.guild.id]:
            self.song_queue[ctx.guild.id][0].SongIn = 0
            await asyncio.sleep(2)
            self.song_queue[ctx.guild.id].clear()
        await ctx.message.add_reaction("👋")
        self.queue_props[ctx.guild.id]["loop"] = LoopType.Disabled

    # Pause
    @commands.command()
    @commands.guild_only()
    async def pause(self, ctx: commands.Context) -> None:
        player = self.client.lavalink.player_manager.get(ctx.guild.id)
        if player.paused is False:
            await player.set_pause(pause=True)
            await ctx.send(f"{ctx.author.display_name} paused `{self.song_queue[ctx.guild.id][0].Title}`")
            # we are adding 1 every second to wait :p
            while player.paused:
                self.song_queue[ctx.guild.id][0].SongIn += 1
                await asyncio.sleep(1)
        else:
            await player.set_pause(pause=False)
            await ctx.send(f"{ctx.author.display_name} resumed `{self.song_queue[ctx.guild.id][0].Title}`")

    # Loop
    @commands.command(aliases=["repeat"])
    @commands.guild_only()
    async def loop(self, ctx: commands.Context, l_type: str = None) -> None:
        loop = self.queue_props[ctx.guild.id]["loop"]
        if l_type is None:
            match loop:
                case LoopType.One | LoopType.All:
                    self.queue_props[ctx.guild.id]["loop"] = LoopType.Disabled
                    embed = Embed(title="Loop Disabled.", colour=0x1ABC9C)
                    await ctx.send(embed=embed)
                case _:
                    self.queue_props[ctx.guild.id]["loop"] = LoopType.All
                    embed = Embed(title="Looping all songs in Queue.", colour=0x800080)
                    await ctx.send(embed=embed)
            return
        if l_type.lower() == "all" or l_type is None and loop == LoopType.Disabled:
            self.queue_props[ctx.guild.id]["loop"] = LoopType.All
            embed = Embed(title="Looping all songs in Queue.", colour=0x800080)
            await ctx.send(embed=embed)
            return
        if l_type.lower() in ["one", "current", "1"]:
            self.queue_props[ctx.guild.id]["loop"] = LoopType.One
            embed = Embed(title="Looping current Song.", colour=0x900090)
            await ctx.send(embed=embed)
            return

    # Now Playing
    @commands.command(aliases=["np"])
    @commands.guild_only()
    async def nowplaying(self, ctx: commands.Context) -> None:
        await ctx.message.delete()
        if not self.song_queue[ctx.guild.id]:
            await ctx.send("Queue is Empty", delete_after=30)
            return
        player = self.client.lavalink.player_manager.get(ctx.guild.id)
        view = NowPlayingButtons(self.song_queue[ctx.guild.id], self.queue_props[ctx.guild.id], player)
        msg = await ctx.send(embed=view.NPEmbed(), view=view)
        view.message = msg
        while True:
            if self.song_queue[ctx.guild.id] and ctx.voice_client:
                pass
            else:
                try:
                    await msg.delete()
                except NotFound:
                    pass
                break
            await msg.edit(embed=view.NPEmbed())
            await asyncio.sleep(5)

    # Jump
    @commands.command(aliases=["skipto"])
    @commands.guild_only()
    async def jump(self, ctx: commands.Context, song_index: int = 1) -> None:
        player = self.client.lavalink.player_manager.get(ctx.guild.id)
        if (
                ctx.voice_client is not None
                and player.is_playing
                and song_index >= 1
        ):
            if song_index >= 2:
                del self.song_queue[ctx.guild.id][1:song_index]
            self.song_queue[ctx.guild.id][0].SongIn = 1
            await asyncio.sleep(2)
            await ctx.send("Skipped")

    # Volume
    @commands.command(aliases=["vol", "v"])
    @commands.guild_only()
    async def volume(self, ctx: commands.Context, volume_int: int = None) -> None:
        player = self.client.lavalink.player_manager.get(ctx.guild.id)
        if volume_int is None:
            await ctx.send(f"Volume: {player.volume}%")
        elif 0 < volume_int <= 100:
            try:
                await player.set_volume(round(volume_int))
                self.queue_props[ctx.guild.id]["volume"] = round(volume_int)
                await ctx.send(f"Volume is set to `{round(volume_int)}%`")
            except AttributeError:
                pass
        else:
            await ctx.send("Set Volume between `1 and 100`.")

    # Add Tags to Current Song
    @commands.is_owner()
    @commands.guild_only()
    @commands.command(aliases=["tag"])
    async def addtag(self, ctx: commands.Context, *, tag: str) -> None:
        video_id = vid_id_regex.search(self.song_queue[ctx.guild.id][0].pURL).group(1)
        AddTagstoJSON(video_id, tag)
        await ctx.reply(f"TAG: **{tag}** added to **{self.song_queue[ctx.guild.id][0].Title}**")

    # Check Bot in VC
    @queue.before_invoke
    @skip.before_invoke
    @stop.before_invoke
    @pause.before_invoke
    @loop.before_invoke
    @nowplaying.before_invoke
    @jump.before_invoke
    @addtag.before_invoke
    @volume.before_invoke
    async def check_voice(self, ctx: commands.Context) -> None:
        player = self.client.lavalink.player_manager.get(ctx.guild.id)
        if ctx.voice_client is None or not player.is_connected:
            raise commands.CheckFailure("Bot is not connect to VC.")
        if ctx.author.voice is None:
            raise commands.CheckFailure("You are not connected to a voice channel.")
        if ctx.voice_client is not None and ctx.author.voice is not None:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                raise commands.CheckFailure("You must be in same VC as Bot.")

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
    client.add_cog(Music(client))
