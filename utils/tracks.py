import re

from pyyoutube import Api
from wavelink import Playable

from config import YT_API_KEY
from .presence import remove_brackets

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


def clickable_song(song: Playable) -> str:
    return f"[{remove_brackets(song.title)}]({song.uri})"
