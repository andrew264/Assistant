# Imports
import asyncio

from disnake import (
    Activity,
    ActivityType,
    Client,
    Embed,
    FFmpegPCMAudio,
    PCMVolumeTransformer,
    Status,
    VoiceClient,
)
from disnake.ext import commands
from disnake.utils import get

from cogs.music.fetch import (
    FindInputType,
    InputType,
    FetchVideo,
    Search,
    FetchPlaylist,
    StreamURL,
    vid_id_regex,
)
from cogs.music.loop import LoopType
from cogs.music.misc import AddTagstoJSON
from cogs.music.nowplaying import NowPlayingButtons, NPEmbed
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

    # Play
    @commands.command(pass_context=True, aliases=["p"])
    @commands.guild_only()
    async def play(self, ctx: commands.Context, *, query: str = None) -> None:

        # create Dictionary
        if ctx.guild.id not in self.song_queue:
            self.song_queue[ctx.guild.id] = []
            self.queue_props[ctx.guild.id] = {
                "volume": 0.25,
                "loop": LoopType.Disabled
            }

        # If player is_paused resume...
        if query is None:
            if (
                    self.song_queue[ctx.guild.id]
                    and isinstance(ctx.voice_client, VoiceClient)
                    and ctx.voice_client.is_paused() is True
            ):
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
                    video_info = await loop.run_in_executor(None, FetchPlaylist, query, ctx.author.display_name)
                    self.song_queue[ctx.guild.id].extend(video_info)
                case InputType.Search:
                    video_info = await loop.run_in_executor(None, Search, query, ctx.author.display_name)
                    self.song_queue[ctx.guild.id].append(video_info)
                case InputType.URL:
                    video_info = await loop.run_in_executor(None, FetchVideo, query, ctx.author.display_name)
                    self.song_queue[ctx.guild.id].append(video_info)

        if input_type == InputType.Playlist:
            await ctx.send(f"Adding Playlist to Queue...")
        else:
            await ctx.send(f"Adding `{self.song_queue[ctx.guild.id][-1].Title}` to Queue.")

        # Join VC
        voice = get(self.client.voice_clients, guild=ctx.guild)
        if voice and voice.is_connected():
            pass
        elif voice is None:
            voice_channel = ctx.author.voice.channel
            await voice_channel.connect()
        if (
                self.song_queue[ctx.guild.id][0]
                and ctx.voice_client.is_paused() is False
                and ctx.voice_client.is_playing() is False
        ):
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
        # get stream url
        loop = asyncio.get_event_loop()
        stream_url = await loop.run_in_executor(None, StreamURL, current_song.pURL)
        # voice
        voice = ctx.voice_client
        if voice is None or voice.is_playing():
            return
        voice.play(FFmpegPCMAudio(stream_url, **FFMPEG_OPTIONS))
        volume = self.queue_props[ctx.guild.id]["volume"]
        voice.source = PCMVolumeTransformer(voice.source, volume)
        # embed
        embed = Embed(title="", color=0xFF0000)
        embed.set_author(name=f"Playing: {current_song.Title}", url=current_song.pURL, icon_url="")
        await ctx.send(embed=embed, delete_after=current_song.Duration)
        # countdown
        while True:
            if self.song_queue[ctx.guild.id] and self.song_queue[ctx.guild.id][0].SongIn > 0:
                self.song_queue[ctx.guild.id][0].SongIn -= 1
            else:
                voice.stop()
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
        if not self.song_queue[ctx.guild.id] or arg > len(self.song_queue[ctx.guild.id]):
            return
        await ctx.send(f"{ctx.author.display_name} removed `{self.song_queue[ctx.guild.id][arg].Title}` from Queue.")
        if 0 < arg <= len(self.song_queue[ctx.guild.id]):
            self.song_queue[ctx.guild.id].pop(arg)
        elif arg == 0:
            ctx.voice_client.stop()
            self.song_queue[ctx.guild.id][0].SongIn = 0
            await asyncio.sleep(1)

    # Stop
    @commands.command(aliases=["dc", "kelambu"])
    @commands.guild_only()
    async def stop(self, ctx: commands.Context) -> None:
        if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
            ctx.voice_client.stop()
        # clean list
        if self.song_queue and self.song_queue[ctx.guild.id]:
            self.song_queue[ctx.guild.id][0].SongIn = 0
            await asyncio.sleep(2)
            self.song_queue[ctx.guild.id].clear()
        await ctx.message.add_reaction("👋")
        await ctx.voice_client.disconnect(force=True)
        self.queue_props[ctx.guild.id]["loop"] = LoopType.Disabled

    # Pause
    @commands.command()
    @commands.guild_only()
    async def pause(self, ctx: commands.Context) -> None:
        if ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send(f"{ctx.author.display_name} paused `{self.song_queue[ctx.guild.id][0].Title}`")
            # we are adding 1 every second to wait :p
            while ctx.voice_client.is_paused():
                self.song_queue[ctx.guild.id][0].SongIn += 1
                await asyncio.sleep(1)
        else:
            ctx.voice_client.resume()
            await ctx.send(f"{ctx.author.display_name} resumed `{self.song_queue[ctx.guild.id][0].Title}`")

    # Loop
    @commands.command(aliases=["repeat"])
    @commands.guild_only()
    async def loop(self, ctx: commands.Context, l_type: str = None) -> None:
        loop = self.queue_props[ctx.guild.id]["loop"]
        if l_type is None and loop == LoopType.One or loop == LoopType.All:
            self.queue_props[ctx.guild.id]["loop"] = LoopType.Disabled
            embed = Embed(title="Loop Disabled.", colour=0x1ABC9C)
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
        view = NowPlayingButtons(self.song_queue[ctx.guild.id])
        msg = await ctx.send(embed=NPEmbed(self.song_queue[ctx.guild.id][0], ctx.voice_client), view=view)
        view.message = msg
        while True:
            if self.song_queue[ctx.guild.id] and ctx.voice_client:
                pass
            else:
                break
            await msg.edit(embed=NPEmbed(self.song_queue[ctx.guild.id][0], ctx.voice_client))
            await asyncio.sleep(5)

    # Jump
    @commands.command(aliases=["skipto"])
    @commands.guild_only()
    async def jump(self, ctx: commands.Context, song_index: int = 1) -> None:
        if (
                ctx.voice_client is not None
                and ctx.voice_client.is_playing()
                or ctx.voice_client.is_paused()
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
        if volume_int is None:
            await ctx.send(f"Volume: {round(ctx.voice_client.source.volume * 100)}%")
        elif 0 < volume_int <= 100:
            try:
                ctx.voice_client.source.volume = round(volume_int) / 100
                self.queue_props[ctx.guild.id]["volume"] = ctx.voice_client.source.volume
                await ctx.send(f"Volume is set to `{round(ctx.voice_client.source.volume * 100)}%`")
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
        if ctx.voice_client is None or not ctx.voice_client.is_connected():
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


def setup(client):
    client.add_cog(Music(client))
