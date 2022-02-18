from typing import Optional

import disnake
from lavalink import AudioTrack
from pyyoutube import Api

from EnvVariables import YT_TOKEN
from assistant import human_int

api = Api(api_key=YT_TOKEN)


class VideoTrack(AudioTrack):

    def __init__(self, data: dict, author: disnake.Member, **extra):
        super().__init__(data, author.id, **extra)
        self.author = author
        self.thumbnail: Optional[str] = None
        self._views: Optional[int] = None
        self._likes: Optional[int] = None
        self.upload_date: Optional[str] = None

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
    def avatar_url(self):
        """Author's Avatar URL"""
        return self.author.display_avatar.url

    @property
    def requested_by(self):
        """The user who requested the track"""
        return self.author.display_name

    @property
    def views(self):
        """Video Views in Human readable format"""
        return human_int(int(self._views))

    @property
    def likes(self):
        """Video Likes in Human readable format"""
        return human_int(int(self._likes))

    def fetch_info(self) -> None:
        """Fetch the video info from YouTube"""
        if self.thumbnail:
            return
        video_data = api.get_video_by_id(video_id=self.identifier).items[0]
        thumbnails = video_data.snippet.thumbnails
        self.thumbnail = thumbnails.maxres.url if thumbnails.maxres else thumbnails.default.url
        self._views = video_data.statistics.viewCount
        self._likes = video_data.statistics.likeCount
        self.upload_date = video_data.snippet.string_to_datetime(video_data.snippet.publishedAt).strftime("%d-%m-%Y")
