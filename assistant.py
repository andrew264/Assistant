import asyncio
from pathlib import Path
from typing import Optional

import discord
import wavelink
from discord import utils
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from config import DATABASE_NAME, TEST_GUILDS, MONGO_URI, LAVA_CONFIG, LOG_LEVEL
from utils import get_logger


class AssistantBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = get_logger(name="Assistant", level=LOG_LEVEL)
        self.start_time = utils.utcnow()
        self._mongo_db: Optional[AsyncIOMotorClient] = None

    async def setup_hook(self) -> None:
        await self.connect_to_mongo()
        for folder in Path("cogs").iterdir():
            if folder.is_dir():
                # Skip tasks folder. it's annoying to debug with it.
                if LOG_LEVEL == "DEBUG" and folder.name == "tasks":
                    self.logger.warning(f"[SKIPPED] - {folder.name}, reason: DEBUG mode")
                    continue
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

        if LAVA_CONFIG:
            nodes = [
                wavelink.Node(uri=LAVA_CONFIG.uri, password=LAVA_CONFIG.password, inactive_player_timeout=300, ),
            ]
            await wavelink.Pool.connect(nodes=nodes, client=self, cache_capacity=None)
            self.logger.info("[LAVALINK] Connected.")
        else:
            self.logger.warning("[LAVALINK] Configuration not found.")

    @property
    def database(self) -> AsyncIOMotorClient:
        assert self._mongo_db
        return self._mongo_db

    async def connect_to_mongo(self) -> Optional[AsyncIOMotorClient]:
        """
        Connects to MongoDB
        """
        if not MONGO_URI:
            return None
        RETRY_ATTEMPTS = 3
        RETRY_DELAY = 5

        for attempt in range(RETRY_ATTEMPTS):
            try:
                self.logger.info(f"[CONNECTING] to MongoDB Database: {DATABASE_NAME}... (Attempt {attempt + 1})")
                self._mongo_db = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=20000)
                await self._mongo_db.admin.command('ping')
                self.logger.info("[CONNECTED] to MongoDB.")
                return self._mongo_db
            except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                self.logger.error(f"[FAILED] MongoDB Connection Attempt {attempt + 1}: {e}")
                if attempt < RETRY_ATTEMPTS - 1:
                    self.logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                    await asyncio.sleep(RETRY_DELAY)
                else:
                    raise Exception("Failed to connect to MongoDB after multiple attempts.")

        return self._mongo_db
