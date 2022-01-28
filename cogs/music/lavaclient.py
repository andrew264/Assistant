from typing import Optional

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

    async def disconnect(self, *, force: bool = True) -> None:
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

    def __init__(self, data: dict, author: Member, **extra):
        super().__init__(data, author.id, **extra)
        self.Author = author
        self.thumbnail: Optional[str] = None
        self.views: Optional[int] = None
        self.likes: Optional[int] = None
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

    def fetch_info(self) -> None:
        """Fetch the video info from YouTube"""
        if self.thumbnail:
            return
        video_data = api.get_video_by_id(video_id=self.identifier).items[0]
        thumbnails = video_data.snippet.thumbnails
        self.thumbnail = thumbnails.maxres.url if thumbnails.maxres else thumbnails.default.url
        self.views = video_data.statistics.viewCount
        self.likes = video_data.statistics.likeCount
        self.upload_date = video_data.snippet.string_to_datetime(video_data.snippet.publishedAt).strftime("%d-%m-%Y")
