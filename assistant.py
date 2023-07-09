from pathlib import Path
from typing import Optional

import discord
import wavelink
from discord import utils
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
from wavelink.ext import spotify

from config import logger, TEST_GUILDS, MONGO_URI, LavaConfig, SpotifyConfig


class AssistantBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logger
        self.start_time = utils.utcnow()
        self._mongo_db: Optional[AsyncIOMotorClient] = None

    async def setup_hook(self) -> None:
        for folder in Path("cogs").iterdir():
            if folder.is_dir():
                for file in folder.iterdir():
                    if file.suffix == ".py":
                        try:
                            await self.load_extension(f"cogs.{folder.name}.{file.stem}")
                        except Exception as e:
                            self.logger.error(f"[FAILED] load - {folder.name}.{file.stem}", exc_info=e)
                        else:
                            self.logger.info(f"[LOADED] - {folder.name}.{file.stem}")

        if TEST_GUILDS:
            guilds = [discord.Object(id=g) for g in TEST_GUILDS]
            for guild in guilds:
                self.logger.info(f"[SYNCING] app_commands to test guild: {guild.id}")
                self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)

        lconf = LavaConfig()
        if lconf:
            sconf = SpotifyConfig()
            if sconf:
                sc = spotify.SpotifyClient(client_id=sconf.CLIENT_ID, client_secret=sconf.CLIENT_SECRET)
                self.logger.info("[LOADED] Spotify Client")
            else:
                sc = None
            self.logger.info("[CONNECTING] to LavaLink...")
            node: wavelink.Node = wavelink.Node(uri=lconf.URI, password=lconf.PASSWORD, )
            await wavelink.NodePool.connect(client=self, nodes=[node], spotify=sc)
            self.logger.info("[CONNECTED] to LavaLink.")
        else:
            self.logger.warning("[FAILED] LavaLink is not configured.")

    def connect_to_mongo(self) -> Optional[AsyncIOMotorClient]:
        """
        Connects to MongoDB
        """
        if not MONGO_URI:
            return None

        if not self._mongo_db:
            try:
                self.logger.info("[CONNECTING] to MongoDB...")
                self._mongo_db = AsyncIOMotorClient(MONGO_URI)
                self._mongo_db.admin.command('ping')
            except (ConnectionFailure, Exception) as e:
                self.logger.error("[FAILED] MongoDB Connection Failed", exc_info=e)
                self._mongo_db = None
            else:
                self.logger.info("[CONNECTED] to MongoDB.")

        return self._mongo_db
