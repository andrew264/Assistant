import re
import time

import disnake
import lavalink
from disnake import Member
from lavalink import AudioTrack
from pyyoutube import Api

from EnvVariables import YT_TOKEN

api = Api(api_key=YT_TOKEN)


class LavalinkVoiceClient(disnake.VoiceClient):
    """
    This is the preferred way to handle external voice sending
    This client will be created via a cls in the connect method of the channel
    """

    def __init__(self, client: disnake.Client, channel: disnake.abc.Connectable):
        self.client = client
        self.channel = channel
        # ensure there exists a client already
        if hasattr(self.client, 'lavalink'):
            self.lavalink = self.client.lavalink
        else:
            self.client.lavalink = lavalink.Client(client.user.id)
            self.client.lavalink.add_node(
                '127.0.0.1',
                2333,
                'youshallnotpass',
                'in',
                'assistant-node')
            self.lavalink = self.client.lavalink

    async def on_voice_server_update(self, data):
        # the data needs to be transformed before being handed down to
        # voice_update_handler
        lavalink_data = {
            't': 'VOICE_SERVER_UPDATE',
            'd': data
        }
        await self.lavalink.voice_update_handler(lavalink_data)

    async def on_voice_state_update(self, data):
        # the data needs to be transformed before being handed down to
        # voice_update_handler
        lavalink_data = {
            't': 'VOICE_STATE_UPDATE',
            'd': data
        }
        await self.lavalink.voice_update_handler(lavalink_data)

    async def connect(self, *, timeout: float, reconnect: bool) -> None:
        """
        Connect the bot to the voice channel and create a player_manager
        if it doesn't exist yet.
        """
        # ensure there is a player_manager when creating a new voice_client
        self.lavalink.player_manager.create(guild_id=self.channel.guild.id)
        await self.channel.guild.change_voice_state(channel=self.channel)

    async def disconnect(self, *, force: bool) -> None:
        """
        Handles the disconnect.
        Cleans up running player and leaves the voice client.
        """
        player = self.lavalink.player_manager.get(self.channel.guild.id)

        # no need to disconnect if we are not connected
        if not force and not player.is_connected:
            return

        # None means disconnect
        await self.channel.guild.change_voice_state(channel=None)

        # update the channel_id of the player to None
        # this must be done because the on_voice_state_update that
        # would set channel_id to None doesn't get dispatched after the
        # disconnect
        player.channel_id = None
        self.cleanup()


class VideoTrack(AudioTrack):

    def __init__(self, data: dict, author: Member, video_id: str = None, video_dict: dict = None, **extra):
        super().__init__(data, author.id, **extra)
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
        else:
            self.Title: str = video_dict["Title"]
            self.pURL: str = video_dict["pURL"]
            self.Thumbnail: str = video_dict["Thumbnail"]
            self.Views: int = int(video_dict["Views"])
            self.Likes: int = int(video_dict["Likes"])
            self.UploadDate: str = video_dict["UploadDate"]
            self.Duration: int = int(video_dict["Duration"])
            self.FDuration: str = video_dict["FDuration"]

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
                "Tags": [],
            }
        }
        if query is not None:
            dict1[video_id]["Tags"] = [query]
        return dict1
