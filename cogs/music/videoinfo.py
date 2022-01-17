import re
import time

from disnake import Member
from pyyoutube import Api

from EnvVariables import YT_TOKEN

api = Api(api_key=YT_TOKEN)


class VideoInfo:
    """Fetch Info from API"""

    def __init__(self, video_id: str = None, video_dict: dict = None, author: Member = None) -> None:
        self.Author = author
        if video_id is not None:
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
            self.UploadDate: str = video_data.snippet.string_to_datetime(video_data.snippet.publishedAt).strftime(
                "%d-%m-%Y")
            self.Duration: int = video_data.contentDetails.get_video_seconds_duration()
            self.FDuration: str = time.strftime("%M:%S", time.gmtime(self.Duration))
            self.SongIn: int = self.Duration
        else:
            self.Title: str = video_dict["Title"]
            self.pURL: str = video_dict["pURL"]
            self.Thumbnail: str = video_dict["Thumbnail"]
            self.Views: int = int(video_dict["Views"])
            self.Likes: int = int(video_dict["Likes"])
            self.UploadDate: str = video_dict["UploadDate"]
            self.Duration: int = int(video_dict["Duration"])
            self.FDuration: str = video_dict["FDuration"]
            self.SongIn: int = int(video_dict["SongIn"])

    def toDict(self, query: str = None) -> dict:
        """returns Video Details as Dictionary"""
        vid_id_regex = re.compile(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*")
        video_id = vid_id_regex.search(self.pURL).group(1)
        dict1: dict = {
            video_id: {
                "Title": self.Title,
                "pURL": self.pURL,
                "Thumbnail": self.Thumbnail,
                "Views": self.Views,
                "Likes": self.Likes,
                "UploadDate": self.UploadDate,
                "Duration": self.Duration,
                "FDuration": self.FDuration,
                "SongIn": self.SongIn,
                "Tags": [],
            }
        }
        if query is not None:
            dict1[video_id]["Tags"] = [query]
        return dict1
