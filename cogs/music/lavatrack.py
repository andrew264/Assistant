from typing import Optional

from disnake import Member
from lavalink import AudioTrack
from pyyoutube import Api

from EnvVariables import YT_TOKEN

api = Api(api_key=YT_TOKEN)


def human_format(num):
    """Convert Integers to Human readable formats."""
    for x in ["", "K", "M", "B", "T"]:
        if num < 1000:
            return "%3.1f %s" % (num, x)
        num /= 1000


class VideoTrack(AudioTrack):

    def __init__(self, data: dict, author: Member, **extra):
        super().__init__(data, author.id, **extra)
        self.Author = author
        self.thumbnail: Optional[str] = None
        self._views: Optional[int] = None
        self._likes: Optional[int] = None
        self.upload_date: Optional[str] = None

    @staticmethod
    def formated_time(ms: float) -> str:
        """Duration in HH:MM:SS Format"""
        seconds = ms / 1000
        if seconds > 3600:
            return f'{int(seconds // 3600)}:{int((seconds % 3600) // 60):02}:{int(seconds % 60):02}'
        else:
            return f'{int(seconds // 60):02}:{int(seconds % 60):02}'

    @property
    def avatar_url(self):
        """Author's Avatar URL"""
        return self.Author.display_avatar.url

    @property
    def views(self):
        """Video Views in Human readable format"""
        return human_format(int(self._views))

    @property
    def likes(self):
        """Video Likes in Human readable format"""
        return human_format(int(self._likes))

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
