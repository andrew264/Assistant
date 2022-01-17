import json
import re
from enum import Enum
from typing import List

import yt_dlp.YoutubeDL as YDL
from disnake import Member
from pyyoutube import Api
from pyyoutube.models.playlist_item import PlaylistItem

from EnvVariables import YT_TOKEN
from cogs.music.lavaclient import VideoTrack

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


async def Search(query: str, author: Member, player) -> None:
    with open("data/MusicCache.json", "r+") as jsonFile:
        data: dict = json.load(jsonFile)
        for video_id in data:
            if (query.lower() in data[video_id]["Title"].lower()
                    or "Tags" in data[video_id]
                    and query.lower() in data[video_id]["Tags"]):
                jsonFile.close()
                result = (await player.node.get_tracks(data[video_id]["pURL"]))['tracks'][0]
                track = VideoTrack(data=result, author=author, video_dict=data[video_id])
                break
        else:
            with YDL(ydl_opts) as ydl:
                video_id = ydl.extract_info(f"ytsearch:{query}", download=False)["entries"][0]["id"]
            result = (await player.node.get_tracks(f"https://www.youtube.com/watch?v={video_id}"))['tracks'][0]
            track = VideoTrack(data=result, author=author, video_id=video_id)
            data.update(track.toDict(query))
            jsonFile.seek(0)
            json.dump(data, jsonFile, indent=4, sort_keys=True)
            jsonFile.close()
        player.add(requester=author.id, track=track)


async def FetchVideo(query: str, author: Member, player) -> None:
    video_id = vid_id_regex.search(query).group(1)
    result = (await player.node.get_tracks(query))['tracks'][0]
    with open("data/MusicCache.json", "r+") as jsonFile:
        data: dict = json.load(jsonFile)
        if video_id in data:
            jsonFile.close()
            track = VideoTrack(data=result, author=author, video_dict=data[video_id])
        else:
            track = VideoTrack(data=result, author=author, video_id=video_id)
            data.update(track.toDict())
            jsonFile.seek(0)
            json.dump(data, jsonFile, indent=4, sort_keys=True)
            jsonFile.close()
        player.add(requester=author.id, track=track)


async def FetchPlaylist(query: str, author: Member, player) -> None:
    playlist_id = query.replace("https://www.youtube.com/playlist?list=", "")
    video_items: List[PlaylistItem] = api.get_playlist_items(playlist_id=playlist_id, count=None).items
    video_ids = [video.snippet.resourceId.videoId for video in video_items]
    with open("data/MusicCache.json", "r+") as jsonFile:
        data: dict = json.load(jsonFile)
        for video_id in video_ids:
            result = (await player.node.get_tracks(f"https://www.youtube.com/watch?v={video_id}"))['tracks'][0]
            if video_id in data:
                track = VideoTrack(data=result, author=author, video_dict=data[video_id])
            else:
                track = VideoTrack(data=result, author=author, video_id=video_id)
                data.update(track.toDict())
            player.add(requester=author.id, track=track)
        jsonFile.seek(0)
        json.dump(data, jsonFile, indent=4, sort_keys=True)
        jsonFile.close()
