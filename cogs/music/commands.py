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
        self.looper: bool = False
        self.dict_obj: dict = {}
        self.volume_float: float = 0.25

    # Play
    @commands.command(pass_context=True, aliases=["p"])
    @commands.guild_only()
    async def play(self, ctx: commands.Context, *, query: str = None) -> None:

        # create Dictionary
        if ctx.guild is None:
            return
        if not self.dict_obj:
            for guild in self.client.guilds:
                self.dict_obj[guild.id] = []

        # If player is_paused resume...
        if query is None:
            if (
                    self.dict_obj[ctx.guild.id]
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
                    self.dict_obj[ctx.guild.id].extend(video_info)
                case InputType.Search:
                    video_info = await loop.run_in_executor(None, Search, query, ctx.author.display_name)
                    self.dict_obj[ctx.guild.id].append(video_info)
                case InputType.URL:
                    video_info = await loop.run_in_executor(None, FetchVideo, query, ctx.author.display_name)
                    self.dict_obj[ctx.guild.id].append(video_info)

        if input_type == InputType.Playlist:
            await ctx.send(f"Adding Playlist to Queue...")
        else:
            await ctx.send(f"Adding `{self.dict_obj[ctx.guild.id][-1].Title}` to Queue.")

        # Join VC
        voice = get(self.client.voice_clients, guild=ctx.guild)
        if voice and voice.is_connected():
            pass
        elif voice is None:
            voice_channel = ctx.author.voice.channel
            await voice_channel.connect()
        if (
                self.dict_obj[ctx.guild.id][0]
                and ctx.voice_client.is_paused() is False
                and ctx.voice_client.is_playing() is False
        ):
            await self.player(ctx)

    # Queue
    @commands.command(aliases=["q"])
    @commands.guild_only()
    async def queue(self, ctx: commands.Context) -> None:
        view = QueuePages(self.dict_obj[ctx.guild.id])
        view.message = await ctx.send(embed=QueueEmbed(self.dict_obj[ctx.guild.id], 1), view=view)

    # Play from Queue
    async def player(self, ctx: commands.Context) -> None:
        await self.StatusUpdate(ctx)
        if not self.dict_obj[ctx.guild.id]:
            return
        current_song: VideoInfo = self.dict_obj[ctx.guild.id][0]
        # get stream url
        loop = asyncio.get_event_loop()
        stream_url = await loop.run_in_executor(None, StreamURL, self.dict_obj[ctx.guild.id][0].pURL)
        # voice
        voice = ctx.voice_client
        if voice is None or voice.is_playing():
            return
        voice.play(FFmpegPCMAudio(stream_url, **FFMPEG_OPTIONS))
        voice.source = PCMVolumeTransformer(voice.source, self.volume_float)
        # embed
        embed = Embed(title="", color=0xFF0000)
        embed.set_author(name=f"Playing: {current_song.Title}", url=current_song.pURL, icon_url="")
        await ctx.send(embed=embed, delete_after=current_song.Duration)
        # countdown
        while self.dict_obj[ctx.guild.id][0].SongIn > 0:
            await asyncio.sleep(1)
            self.dict_obj[ctx.guild.id][0].SongIn -= 1
        # stop the player
        voice.stop()
        # song ends here
        if self.dict_obj[ctx.guild.id] and self.looper:
            self.dict_obj[ctx.guild.id].append(self.dict_obj[ctx.guild.id][0])
            self.dict_obj[ctx.guild.id].pop(0)
            # Temp Fix
            self.dict_obj[ctx.guild.id][0].SongIn = self.dict_obj[ctx.guild.id][0].Duration
        elif self.dict_obj[ctx.guild.id] and not self.looper:
            self.dict_obj[ctx.guild.id].pop(0)
        await self.player(ctx)

    # Update client's status
    # Cuz why not ?
    async def StatusUpdate(self, ctx: commands.Context) -> None:
        if self.dict_obj[ctx.guild.id]:
            await self.client.change_presence(
                activity=Activity(type=ActivityType.listening, name=self.dict_obj[ctx.guild.id][0].Title, ))
        else:
            await self.client.change_presence(status=Status.online,
                                              activity=Activity(type=ActivityType.watching, name="yall Homies."), )

    # Skip
    @commands.command()
    @commands.guild_only()
    async def skip(self, ctx: commands.Context, arg: int = 0) -> None:
        if not self.dict_obj[ctx.guild.id] or arg > len(self.dict_obj[ctx.guild.id]):
            return
        await ctx.send(f"{ctx.author.display_name} removed `{self.dict_obj[ctx.guild.id][arg].Title}` from Queue.")
        if 0 < arg <= len(self.dict_obj[ctx.guild.id]):
            self.dict_obj[ctx.guild.id].pop(arg)
        elif arg == 0:
            ctx.voice_client.stop()
            self.dict_obj[ctx.guild.id][0].SongIn = 0
            await asyncio.sleep(1)

    # Stop
    @commands.command(aliases=["dc", "kelambu"])
    @commands.guild_only()
    async def stop(self, ctx: commands.Context) -> None:
        if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
            ctx.voice_client.stop()
        # clean list
        if self.dict_obj and self.dict_obj[ctx.guild.id]:
            self.dict_obj[ctx.guild.id][0].SongIn = 0
            await asyncio.sleep(2)
            self.dict_obj[ctx.guild.id].clear()
        await ctx.message.add_reaction("👋")
        await ctx.voice_client.disconnect(force=True)
        self.looper = False

    # Pause
    @commands.command()
    @commands.guild_only()
    async def pause(self, ctx: commands.Context) -> None:
        if ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send(f"{ctx.author.display_name} paused `{self.dict_obj[ctx.guild.id][0].Title}`")
            # we are adding 1 every second to wait :p
            while ctx.voice_client.is_paused():
                self.dict_obj[ctx.guild.id][0].SongIn += 1
                await asyncio.sleep(1)
        else:
            ctx.voice_client.resume()
            await ctx.send(f"{ctx.author.display_name} resumed `{self.dict_obj[ctx.guild.id][0].Title}`")

    # Loop
    @commands.command(aliases=["repeat"])
    @commands.guild_only()
    async def loop(self, ctx: commands.Context) -> None:
        if self.looper:
            self.looper = False
            embed = Embed(title="Loop Disabled.", colour=0x1ABC9C)
        else:
            self.looper = True
            embed = Embed(title="Loop Enabled.", colour=0x800080)
        await ctx.send(embed=embed)

    # Now Playing
    @commands.command(aliases=["np"])
    @commands.guild_only()
    async def nowplaying(self, ctx: commands.Context) -> None:
        await ctx.message.delete()
        song_queue: list[VideoInfo] = self.dict_obj[ctx.guild.id]
        if not song_queue:
            await ctx.send("Queue is Empty", delete_after=30)
            return
        view = NowPlayingButtons(song_queue)
        msg = await ctx.send(embed=NPEmbed(song_queue[0], ctx.voice_client), view=view)
        view.message = msg
        while True:
            if self.dict_obj[ctx.guild.id] and ctx.voice_client:
                pass
            else:
                break
            await msg.edit(embed=NPEmbed(song_queue[0], ctx.voice_client))
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
                del self.dict_obj[ctx.guild.id][1:song_index]
            self.dict_obj[ctx.guild.id][0].SongIn = 1
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
                self.volume_float = ctx.voice_client.source.volume
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
        video_id = vid_id_regex.search(self.dict_obj[ctx.guild.id][0].pURL).group(1)
        AddTagstoJSON(video_id, tag)
        await ctx.reply(f"TAG: **{tag}** added to **{self.dict_obj[ctx.guild.id][0].Title}**")

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
