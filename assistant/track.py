from datetime import datetime
from typing import Optional

import disnake
from lavalink import AudioTrack
from pyyoutube import Api, Video

from EnvVariables import YT_TOKEN
from assistant import human_int

api = Api(api_key=YT_TOKEN)


class VideoTrack(AudioTrack):

    def __init__(self, data: dict, author: disnake.Member, **extra):
        super().__init__(data, author.id, **extra)
        self.author = author
        self._views: Optional[int] = None
        self._likes: Optional[int] = None
        self._upload_date: Optional[datetime] = None

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
        return self.author.display_avatar.url

    @property
    def requested_by(self) -> str:
        """The user who requested the track"""
        return self.author.display_name

    @property
    def thumbnail(self) -> str:
        """Video Thumbnail URL"""
        return f"https://i.ytimg.com/vi/{self.identifier}/hqdefault.jpg"

    @property
    def views(self) -> str:
        """Video Views in Human readable format"""
        if not self._views:
            self.fetch_info()
        return human_int(int(self._views))

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
        video_data: Video = api.get_video_by_id(video_id=self.identifier).items[0]
        self._views = video_data.statistics.viewCount
        self._likes = video_data.statistics.likeCount
        self._upload_date = video_data.snippet.string_to_datetime(video_data.snippet.publishedAt)
