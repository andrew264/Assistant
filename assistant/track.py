from datetime import datetime
from typing import Optional, Union

import disnake
from lavalink import AudioTrack
from pyyoutube import Api, Video, VideoListResponse

from assistant import human_int
from config import yt_token

api = Api(api_key=yt_token) if yt_token else None


class TrackInfo:
    def __init__(self, author: Union[disnake.Member, disnake.User,], data: AudioTrack):
        self.author: Optional[disnake.Member | disnake.User] = author
        self._views: Optional[int] = None
        self._likes: Optional[int] = None
        self._upload_date: Optional[datetime] = None
        self.title: str = data.title
        self.uri: str = data.uri
        self.identifier: str = data.identifier

    def __str__(self):
        return f"[{self.title}]({self.uri} \"by {self.requested_by}\")"

    @staticmethod
    def format_time(ms: float) -> str:
        """Duration in HH:MM:SS Format"""
        seconds = ms / 1000
        if seconds > 3600:
            return f'{int(seconds // 3600)}:{int((seconds % 3600) // 60):02}:{int(seconds % 60):02}'
        else:
            return f'{int(seconds // 60):02}:{int(seconds % 60):02}'

    @property
    def avatar_url(self) -> str:
        """Author's Avatar URL"""
        return self.author.display_avatar.url if isinstance(self.author, (disnake.Member, disnake.User)) else ""

    @property
    def requested_by(self) -> str:
        """The user who requested the track"""
        if isinstance(self.author, disnake.Member):
            return str(self.author)
        else:
            return ""

    @property
    def thumbnail(self) -> str:
        """Video Thumbnail URL"""
        return f"https://i.ytimg.com/vi/{self.identifier}/hqdefault.jpg"

    @property
    def views(self) -> str:
        """Video Views in Human readable format"""
        if not self._views:
            self.fetch_info()
        return human_int(int(self._views) if self._views else 0)

    @property
    def likes(self) -> str:
        """Video Likes in Human readable format"""
        if self._likes:
            return human_int(int(self._likes))
        else:
            return "Disabled"

    @property
    def upload_date(self) -> str:
        """Video Upload Date"""
        if self._upload_date:
            return f"<t:{int(self._upload_date.timestamp())}:R>"
        else:
            return "Not Available"

    def fetch_info(self) -> None:
        """Fetch the video info from YouTube"""
        if not api:
            return
        videos: VideoListResponse = api.get_video_by_id(video_id=self.identifier) # type: ignore
        if not videos.items:
            return
        video_data: Video = videos.items[0]
        self._views = video_data.statistics.viewCount
        self._likes = video_data.statistics.likeCount
        self._upload_date = video_data.snippet.string_to_datetime(video_data.snippet.publishedAt)
