# Imports
import asyncio
import json
import math
import re
import time
from enum import Enum
from typing import List

import disnake
import yt_dlp.YoutubeDL as YDL
from disnake import (
    Activity,
    ActivityType,
    Button,
    ButtonStyle,
    Client,
    Embed,
    FFmpegPCMAudio,
    Interaction,
    Message,
    PCMVolumeTransformer,
    Status,
    VoiceClient,
    VoiceProtocol,
)
from disnake.ext import commands
from disnake.utils import get
from pyyoutube import Api
from pyyoutube.models.playlist_item import PlaylistItem

from EnvVariables import YT_TOKEN

api = Api(api_key=YT_TOKEN)

ydl_opts = {
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
    "format": "bestaudio/best",
}
FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -multiple_requests 1",
    "options": "-vn",
}

vid_url_regex = re.compile(r"^(https?\:\/\/)?(www\.)?(youtube\.com|youtu\.?be)\/.+$", re.IGNORECASE)
vid_id_regex = re.compile(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*")
playlist_url_regex = re.compile(r"^(https?\:\/\/)?(www\.)?(youtube\.com)\/(playlist).+$", re.IGNORECASE)


def human_format(num):
    """Convert Integers to Human readable formats."""
    num = float("{:.3g}".format(num))
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return "{}{}".format(
        "{:f}".format(num).rstrip("0").rstrip("."), ["", "K", "M", "B", "T"][magnitude]
    )


class InputType(Enum):
    """
    Types of Input
    Search = 0
    URL = 1
    Playlist = 2
    """

    Search = 0
    URL = 1
    Playlist = 2


class VideoInfo:
    """Fetch Info from API"""

    def __init__(self, video_id: str, author: str):
        video_data = api.get_video_by_id(video_id=video_id).items[0]
        self.Title: str = video_data.snippet.title
        self.pURL: str = f"https://www.youtube.com/watch?v={video_data.id}"
        thumbnails = video_data.snippet.thumbnails
        if thumbnails.maxres:
            self.Thumbnail: str = thumbnails.maxres.url
        else:
            self.Thumbnail: str = thumbnails.default.url
        self.Views: int = video_data.statistics.viewCount
        self.Likes: int = video_data.statistics.likeCount
        self.UploadDate: str = video_data.snippet.string_to_datetime(
            video_data.snippet.publishedAt
        ).strftime("%d-%m-%Y")
        self.Duration: int = video_data.contentDetails.get_video_seconds_duration()
        self.FDuration: str = time.strftime("%M:%S", time.gmtime(self.Duration))
        self.SongIn: int = self.Duration
        self.Author: str = author


class VideoInfofromDict:
    """Cast Dict to Object"""

    def __init__(self, data: dict, author: str):
        self.Title: str = data["Title"]
        self.pURL: str = data["pURL"]
        self.Thumbnail: str = data["Thumbnail"]
        self.Views: int = int(data["Views"])
        self.Likes: int = int(data["Likes"])
        self.UploadDate: str = data["UploadDate"]
        self.Duration: int = int(data["Duration"])
        self.FDuration: str = data["FDuration"]
        self.SongIn: int = int(data["SongIn"])
        self.Author: str = author


def VideoInfotoDict(video: VideoInfo, query: str | None) -> dict:
    """returns Video Details as Dictionary"""
    video_id = vid_id_regex.search(video.pURL).group(1)
    dict1: dict = {
        video_id: {
            "Title": video.Title,
            "pURL": video.pURL,
            "Thumbnail": video.Thumbnail,
            "Views": video.Views,
            "Likes": video.Likes,
            "UploadDate": video.UploadDate,
            "Duration": video.Duration,
            "FDuration": video.FDuration,
            "SongIn": video.SongIn,
            "Tags": [],
        }
    }
    if query is not None:
        dict1[video_id]["Tags"] = [query]
    return dict1


def FindInputType(query: str):
    if re.match(playlist_url_regex, query) is not None:
        return InputType.Playlist
    elif re.match(vid_url_regex, query) is not None:
        return InputType.URL
    else:
        return InputType.Search


def Search(query: str, author: str) -> (VideoInfo | VideoInfofromDict):
    with open("data/MusicCache.json", "r+") as jsonFile:
        data: dict = json.load(jsonFile)
        for video_id in data:
            if (
                    query.lower() in data[video_id]["Title"].lower()
                    or "Tags" in data[video_id]
                    and query.lower() in data[video_id]["Tags"]
            ):
                jsonFile.close()
                return VideoInfofromDict(data=data[video_id], author=author)
        with YDL(ydl_opts) as ydl:
            video_id = ydl.extract_info(f"ytsearch:{query}", download=False)["entries"][0]["id"]
        video_info = VideoInfo(video_id, author)
        data.update(VideoInfotoDict(video_info, query))
        jsonFile.seek(0)
        json.dump(data, jsonFile, indent=4, sort_keys=True)
        jsonFile.close()
        return video_info


def FetchVideo(query: str, author: str) -> (VideoInfo | VideoInfofromDict):
    video_id = vid_id_regex.search(query).group(1)
    with open("data/MusicCache.json", "r+") as jsonFile:
        data: dict = json.load(jsonFile)
        if video_id in data:
            jsonFile.close()
            return VideoInfofromDict(data=data[video_id], author=author)
        else:
            video_info = VideoInfo(video_id, author)
            data.update(VideoInfotoDict(video_info, None))
            jsonFile.seek(0)
            json.dump(data, jsonFile, indent=4, sort_keys=True)
            jsonFile.close()
            return video_info


def FetchPlaylist(query: str, author: str) -> list[VideoInfo | VideoInfofromDict]:
    playlist_videos: List[VideoInfo | VideoInfofromDict] = []
    playlist_id = query.replace("https://www.youtube.com/playlist?list=", "")
    video_items: List[PlaylistItem] = api.get_playlist_items(
        playlist_id=playlist_id, count=None
    ).items
    video_ids = [video.snippet.resourceId.videoId for video in video_items]
    with open("data/MusicCache.json", "r+") as jsonFile:
        data: dict = json.load(jsonFile)
        for video_id in video_ids:
            if video_id in data:
                playlist_videos.append(VideoInfofromDict(data=data[video_id], author=author))
            else:
                video_info = VideoInfo(video_id, author)
                playlist_videos.append(video_info)
                data.update(VideoInfotoDict(video_info, None))
        jsonFile.seek(0)
        json.dump(data, jsonFile, indent=4, sort_keys=True)
        jsonFile.close()
        return playlist_videos


def AddTagstoJSON(video_id: str, tag: str):
    """Add Tags to Videos for Search"""
    with open("data/MusicCache.json", "r+") as jsonFile:
        data: dict = json.load(jsonFile)
        data[video_id]["Tags"].append(tag.lower())
        jsonFile.seek(0)
        json.dump(data, jsonFile, indent=4, sort_keys=True)
        jsonFile.close()


def StreamURL(url: str) -> str:
    """Fetch Stream URL"""
    with YDL(ydl_opts) as ydl:
        formats: list = ydl.extract_info(url, download=False)["formats"]
        return next((f["url"] for f in formats if f["format_id"] == "251"), None)


def QueueEmbed(song_list: list, page_no) -> Embed:
    first = (page_no * 4) - 3
    if (page_no * 4) + 1 <= len(song_list):
        last = (page_no * 4) + 1
    else:
        last = len(song_list)
    song_index = [i for i in range(first, last)]
    if not song_list:
        return Embed(title="Queue is Empty", colour=0xFFA31A)
    embed = Embed(
        title="Now Playing",
        description=f"[{song_list[0].Title}]({song_list[0].pURL} \"by {song_list[0].Author}\")",
        colour=0xFFA31A,
    )
    if len(song_list) > 1:
        next_songs = "\u200b"
        max_page = math.ceil((len(song_list) - 1) / 4)
        for i in song_index:
            next_songs += f"{i}. [{song_list[i].Title}]({song_list[i].pURL} \"by {song_list[i].Author}\")\n"
        embed.add_field(name=f"Next Up ({page_no}/{max_page})", value=next_songs, inline=False)
    return embed


def NPEmbed(
        current_song: VideoInfo | VideoInfofromDict, voice_client: VoiceProtocol
) -> Embed:
    percentile = 20 - round((current_song.SongIn / current_song.Duration) * 20)
    bar = "────────────────────"
    progress_bar = bar[:percentile] + "⚪" + bar[percentile + 1:]
    song_on = time.strftime("%M:%S", time.gmtime(current_song.Duration - current_song.SongIn))
    embed = Embed(color=0xEB459E)
    embed.set_thumbnail(url=f"{current_song.Thumbnail}")
    embed.set_author(name=f"{current_song.Title}", url=current_song.pURL, icon_url="")
    embed.add_field(
        name=f"{song_on} {progress_bar} {current_song.FDuration}",
        value="\u200b",
        inline=False,
    )
    embed.add_field(name="Views:", value=f"{human_format(int(current_song.Views))}", inline=True)
    embed.add_field(name="Likes:", value=f"{human_format(int(current_song.Likes))}", inline=True)
    embed.add_field(name="Uploaded on:", value=f"{current_song.UploadDate}", inline=True)
    if voice_client.is_playing() and voice_client.source:
        embed.set_footer(text=f"Playing (Volume: {round(voice_client.source.volume * 100)}%)")
    elif voice_client.is_paused() and voice_client.source:
        embed.set_footer(text=f"Paused (Volume: {round(voice_client.source.volume * 100)}%)")
    return embed


class QueuePages(disnake.ui.View):
    def __init__(self, obj):
        super().__init__(timeout=60.0)
        self.page_no = 1
        self.obj = obj
        self.message: Message | None = None

    async def on_timeout(self):
        await self.message.edit(view=None)
        self.stop()

    @disnake.ui.button(emoji="◀", style=ButtonStyle.secondary)
    async def prev_page(self, button: Button, interaction: Interaction):
        if self.page_no > 1:
            self.page_no -= 1
        else:
            self.page_no = math.ceil((len(self.obj) - 1) / 4)
        await interaction.response.edit_message(embed=QueueEmbed(self.obj, self.page_no), view=self)

    @disnake.ui.button(emoji="▶", style=ButtonStyle.secondary)
    async def next_page(self, button: Button, interaction: Interaction):
        if self.page_no < math.ceil((len(self.obj) - 1) / 4):
            self.page_no += 1
        else:
            self.page_no = 1
        await interaction.response.edit_message(embed=QueueEmbed(self.obj, self.page_no), view=self)


class NowPlayingButtons(disnake.ui.View):
    def __init__(self, song_queue):
        super().__init__(timeout=120)
        self.message: Message
        self.song_queue: list[VideoInfo | VideoInfofromDict] = song_queue

    async def on_timeout(self):
        try:
            self.stop()
            await self.message.delete()
        except disnake.errors.NotFound:
            pass

    # Pause
    @staticmethod
    async def play_pause(current_song: (VideoInfo | VideoInfofromDict), voice_client: VoiceProtocol) -> None:
        if voice_client.is_playing():
            voice_client.pause()
            while voice_client.is_paused():
                current_song.SongIn += 1
                await asyncio.sleep(1)
        else:
            voice_client.resume()

    @disnake.ui.button(label="Play/Pause", emoji="▶", style=ButtonStyle.primary)
    async def play_button(self, button: Button, interaction: Interaction):
        await interaction.response.edit_message(embed=NPEmbed(self.song_queue[0], interaction.guild.voice_client),
                                                view=self)
        await self.play_pause(self.song_queue[0], interaction.guild.voice_client)

    @disnake.ui.button(label="Skip", emoji="⏭", style=ButtonStyle.primary)
    async def skip_button(self, button: Button, interaction: Interaction):
        interaction.guild.voice_client.stop()
        self.song_queue[0].SongIn = 0
        await interaction.response.edit_message(embed=NPEmbed(self.song_queue[0], interaction.guild.voice_client),
                                                view=self)

    @disnake.ui.button(label="Stop", emoji="⏹", style=ButtonStyle.danger)
    async def stop_button(self, button: Button, interaction: Interaction):
        self.song_queue[0].SongIn = 0
        self.song_queue.clear()
        await interaction.guild.voice_client.disconnect(force=True)
        await interaction.response.edit_message(content="Thanks for Listening", embed=None, view=None)


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
        current_song: (VideoInfo | VideoInfofromDict) = self.dict_obj[ctx.guild.id][0]
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
        song_queue: list[VideoInfo | VideoInfofromDict] = self.dict_obj[ctx.guild.id]
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
            await msg.edit(embed=NPEmbed(song_queue[0], ctx.voice_client), view=view)
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
