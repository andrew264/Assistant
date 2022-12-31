import logging
import os
import signal
import subprocess
from datetime import datetime, timezone
from typing import Optional, Any

import aiosqlite
import disnake
import lavalink
import psutil
from disnake.ext import commands

from assistant import log
from config import LavalinkConfig, database_path, error_channel


class Client(commands.Bot):
    def __init__(self, **options: Any):
        """
        Custom Client class for the Assistant.
        This Inherits from disnake's Bot class.
        """
        super().__init__(**options)
        self.lavalink: Optional[lavalink.Client] = None
        self._db: Optional[aiosqlite.Connection] = None
        self.events = {
            'messages': 0,
            'presence_update': 0,
        }
        self._start_time = datetime.now(timezone.utc)
        self._log_handler: Optional[logging.Logger] = None

        self._lavalink_pid: Optional[int] = None

        # Start Lavalink Server
        self.start_lavalink()
        loop = self.loop
        signal.signal(signal.SIGINT, lambda s, f: loop.create_task(self.close()))

    def start_lavalink(self) -> None:
        """
        Starts the Lavalink Server
        """
        lava_config = LavalinkConfig()
        if lava_config:
            self.logger.info("Starting Lavalink Server...")
            if lava_config.JAVA_PATH:
                env = os.environ.copy()
                env['PATH'] = lava_config.JAVA_PATH + os.pathsep + env['PATH']
            else:
                env = None
            proc = subprocess.Popen(["java", "-Xmx256M", "-Xms256M", "-jar", "Lavalink.jar"],
                                    cwd=lava_config.LAVALINK_PATH,
                                    env=env, shell=True,
                                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                                    )
            self._lavalink_pid = proc.pid
            self.logger.info("Lavalink Server Started.")
            del lava_config
        else:
            self.logger.warning("Lavalink Config not found.")

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
        if self._db is None and database_path:
            self._db = await aiosqlite.connect(database_path)
        return self._db

    async def log(self, content: Optional[str] = None, embed: Optional[disnake.Embed] = None) -> None:
        """
        Logs messages to a Text Channel
        """
        channel = self.get_channel(error_channel)
        if channel is not None:
            await channel.send(content=content, embed=embed)

    async def close(self) -> None:
        """
        Kills the Lavalink Server and closes the Database Connection
        """
        if self._db:
            self.logger.info("Closing Database Connection...")
            await self._db.close()
            self._db = None
            self.logger.info("Database Connection Closed.")
        if self._lavalink_pid:
            self.logger.info("Killing Lavalink Server...")
            process = psutil.Process(self._lavalink_pid)
            for proc in process.children(recursive=True):
                proc.kill()
            process.kill()
            self.logger.info("Lavalink Server Killed.")
            self._lavalink_pid = None
        await super().close()
