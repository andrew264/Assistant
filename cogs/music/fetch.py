import json
import re
from enum import Enum
from typing import List

import yt_dlp.YoutubeDL as YDL
from pyyoutube import Api
from pyyoutube.models.playlist_item import PlaylistItem

from EnvVariables import YT_TOKEN
from cogs.music.videoinfo import VideoInfo

api = Api(api_key=YT_TOKEN)

vid_url_regex = re.compile(r"^(https?\:\/\/)?(www\.)?(youtube\.com|youtu\.?be)\/.+$", re.IGNORECASE)
vid_id_regex = re.compile(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*")
playlist_url_regex = re.compile(r"^(https?\:\/\/)?(www\.)?(youtube\.com)\/(playlist).+$", re.IGNORECASE)

ydl_opts = {
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
    "format": "bestaudio/best",
}


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


def FindInputType(query: str):
    if re.match(playlist_url_regex, query) is not None:
        return InputType.Playlist
    elif re.match(vid_url_regex, query) is not None:
        return InputType.URL
    else:
        return InputType.Search


def Search(query: str, author: str) -> VideoInfo:
    with open("data/MusicCache.json", "r+") as jsonFile:
        data: dict = json.load(jsonFile)
        for video_id in data:
            if (
                    query.lower() in data[video_id]["Title"].lower()
                    or "Tags" in data[video_id]
                    and query.lower() in data[video_id]["Tags"]
            ):
                jsonFile.close()
                return VideoInfo(video_dict=data[video_id], author=author)
        with YDL(ydl_opts) as ydl:
            video_id = ydl.extract_info(f"ytsearch:{query}", download=False)["entries"][0]["id"]
        video_info = VideoInfo(video_id=video_id, author=author)
        data.update(video_info.toDict(query))
        jsonFile.seek(0)
        json.dump(data, jsonFile, indent=4, sort_keys=True)
        jsonFile.close()
        return video_info


def FetchVideo(query: str, author: str) -> VideoInfo:
    video_id = vid_id_regex.search(query).group(1)
    with open("data/MusicCache.json", "r+") as jsonFile:
        data: dict = json.load(jsonFile)
        if video_id in data:
            jsonFile.close()
            return VideoInfo(video_dict=data[video_id], author=author)
        else:
            video_info = VideoInfo(video_id=video_id, author=author)
            data.update(video_info.toDict())
            jsonFile.seek(0)
            json.dump(data, jsonFile, indent=4, sort_keys=True)
            jsonFile.close()
            return video_info


def FetchPlaylist(query: str, author: str) -> list[VideoInfo]:
    playlist_videos: List[VideoInfo] = []
    playlist_id = query.replace("https://www.youtube.com/playlist?list=", "")
    video_items: List[PlaylistItem] = api.get_playlist_items(
        playlist_id=playlist_id, count=None
    ).items
    video_ids = [video.snippet.resourceId.videoId for video in video_items]
    with open("data/MusicCache.json", "r+") as jsonFile:
        data: dict = json.load(jsonFile)
        for video_id in video_ids:
            if video_id in data:
                playlist_videos.append(VideoInfo(video_dict=data[video_id], author=author))
            else:
                video_info = VideoInfo(video_id=video_id, author=author)
                playlist_videos.append(video_info)
                data.update(video_info.toDict())
        jsonFile.seek(0)
        json.dump(data, jsonFile, indent=4, sort_keys=True)
        jsonFile.close()
        return playlist_videos


def StreamURL(url: str) -> str:
    """Fetch Stream URL"""
    with YDL(ydl_opts) as ydl:
        formats: list = ydl.extract_info(url, download=False)["formats"]
        return next((f["url"] for f in formats if f["format_id"] == "251"), None)
