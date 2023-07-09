import asyncio
import re
from datetime import datetime
from typing import Optional, Self, Union

import discord
from pyyoutube import Api, Video
from wavelink import YouTubeTrack, Playable, Playlist, TrackSource, Node, NodePool
from wavelink.ext.spotify import SpotifyTrack

from config import YT_API_KEY

api = Api(api_key=YT_API_KEY) if YT_API_KEY else None

url_rx = re.compile(r'https?://(?:www\.)?.+')
yt_video_rx = r'^(?:https?://(?:www\.)?youtube\.com/watch\?(?=.*v=\w+)(?:\S+)?|https?://youtu\.be/\w+)$'
yt_playlist_rx = r'^https?://(?:www\.)?youtube\.com/playlist\?(?=.*list=\w+)(?:\S+)?$'


def human_int(num) -> str:
    """Convert Integers to Human readable formats."""
    for x in ["", "K", "M", "B", "T"]:
        if num < 1000:
            return f"{num:.1f} {x}"
        num /= 1000
    else:
        return "a lot"


class YTPlaylist(Playable, Playlist):
    PREFIX: str = "ytpl:"

    def __init__(self, data: dict):
        self.tracks: list[YTTrack] = []
        self.name: str = data["playlistInfo"]["name"]
        self._requester: Optional[discord.Member] = None

        self.selected_track: Optional[int] = data["playlistInfo"].get("selectedTrack")
        if self.selected_track is not None:
            self.selected_track = int(self.selected_track)

        for track_data in data["tracks"]:
            track = YTTrack(track_data)
            self.tracks.append(track)

        self.source = TrackSource.YouTube

    def __str__(self) -> str:
        return self.name

    @property
    def requested_by(self) -> Optional[discord.Member]:
        return self._requester

    @requested_by.setter
    def requested_by(self, value: discord.Member) -> None:
        self._requester = value
        for t in self.tracks:
            t.requested_by = value

    @classmethod
    async def search(cls, query: str, /, *, node: Node | None = None) -> Self:
        if re.match(yt_playlist_rx, query):
            tracks = await NodePool.get_playlist(query, cls=cls, node=node)
        else:
            tracks = await NodePool.get_tracks(f'{cls.PREFIX}{query}', cls=cls, node=node)

        return tracks


class YTTrack(YouTubeTrack):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._requester: Optional[discord.Member] = None
        self._views: Optional[int] = None
        self._likes: Optional[int] = None
        self._upload_date: Optional[datetime] = None

    @property
    def requested_by(self) -> Optional[discord.Member]:
        return self._requester

    @requested_by.setter
    def requested_by(self, value: discord.Member) -> None:
        self._requester = value

    @property
    def url(self) -> str:
        return f"https://www.youtube.com/watch?v={self.identifier}"

    @property
    def avatar_url(self) -> str:
        """Author's Avatar URL"""
        return self._requester.display_avatar.url if isinstance(self._requester, discord.Member) else ""

    @property
    def views(self) -> str:
        """Video Views in Human readable format"""
        return human_int(self._views if self._views else 0)

    @property
    def likes(self) -> str:
        """Video Likes in Human readable format"""
        return human_int(self._likes) if self._likes else "Disabled"

    @property
    def upload_date(self) -> str:
        """Video Upload Date"""
        if self._upload_date:
            return f"<t:{int(self._upload_date.timestamp())}:R>"
        else:
            return "Not Available"

    @property
    def thumbnail(self) -> str:
        """Video Thumbnail URL"""
        return f"https://i.ytimg.com/vi/{self.identifier}/hqdefault.jpg"

    @classmethod
    async def search(cls, query: str, /, *, node: Node | None = None) -> Self:
        if re.match(yt_video_rx, query):
            tracks = await NodePool.get_tracks(query, cls=cls, node=node)
        else:
            tracks = await NodePool.get_tracks(f'{cls.PREFIX}{query}', cls=cls, node=node)

        return tracks[0]

    async def fetch_info(self) -> None:
        """Fetch the video info from YouTube"""
        if not api:
            return
        if self._views and self._likes and self._upload_date:
            return

        def _fetch_from_api(_id: str) -> Optional[Video]:
            _videos: VideoListResponse = api.get_video_by_id(video_id=_id)  # type: ignore
            if not _videos.items:
                return None
            _video: Video = _videos.items[0]
            return _video

        loop = asyncio.get_event_loop()
        video_data = await loop.run_in_executor(None, _fetch_from_api, self.identifier)
        if not video_data:
            self._views, self._likes, self._upload_date = 1, 1, datetime.now()
            return

        assert video_data.statistics
        assert video_data.snippet
        self._views = video_data.statistics.viewCount
        self._likes = video_data.statistics.likeCount
        self._upload_date = video_data.snippet.string_to_datetime(video_data.snippet.publishedAt)


def clickable_song(song: Union[Playable, SpotifyTrack]) -> str:
    if isinstance(song, SpotifyTrack):
        return f"[{song.title}](https://open.spotify.com/track/{song.id})"
    return f"[{song.title}](https://www.youtube.com/watch?v={song.identifier})"
