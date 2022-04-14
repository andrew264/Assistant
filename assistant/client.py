import logging
from datetime import datetime, timezone
from typing import Optional, Any

import aiosqlite
import disnake
import lavalink
from disnake.ext import commands

from EnvVariables import DM_Channel
from assistant import log


class Client(commands.Bot):
    def __init__(self, **options: Any):
        """
        Custom Client class for the Assistant.
        This Inherits from disnake's Bot class.
        """
        super().__init__(**options)
        self._lava_host: str = options.get('lava_host')
        self._lava_port: int = options.get('lava_port')
        self._lava_password: str = options.get('lava_password')
        self._lava_region: str = options.get('lava_region')
        self._lava_node_name: str = options.get('lava_node_name')
        self._lavalink: Optional[lavalink.Client] = None
        self._db: Optional[aiosqlite.Connection] = None
        self.events = {
            'messages': 0,
            'socket_send': 0,
            'socket_receive': 0,
            'presence_update': 0,
        }
        self._start_time = datetime.now(timezone.utc)
        self._log_handler: Optional[logging.Logger] = None

    @property
    def lavalink(self):
        """
        Returns the Lavalink Client
        """
        if self._lavalink is None:
            self._lavalink = lavalink.Client(self.user.id)
            self._lavalink.add_node(self._lava_host, self._lava_port,
                                    self._lava_password, self._lava_region, self._lava_node_name)
        return self._lavalink

    @property
    def start_time(self) -> datetime:
        """
        Returns the start time of the bot
        """
        return self._start_time

    @property
    def logger(self) -> logging.Logger:
        """
        Returns the Logger
        """
        if self._log_handler is None:
            self._log_handler = logging.getLogger("Assistant")
            self._log_handler.setLevel(logging.INFO)
            handler = logging.StreamHandler()
            handler.setFormatter(log.CustomFormatter())
            self._log_handler.addHandler(handler)
        return self._log_handler

    async def db_connect(self) -> aiosqlite.Connection:
        """
        Returns the Database Connection
        """
        if self._db is None:
            self._db = await aiosqlite.connect("./data/database.sqlite3")
        return self._db

    async def log(self, content: Optional[str] = None, embed: Optional[disnake.Embed] = None) -> None:
        """
        Logs messages to a Text Channel
        """
        channel = self.get_channel(DM_Channel)
        if channel is not None:
            await channel.send(content=content, embed=embed)
