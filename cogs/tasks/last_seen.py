import datetime
from typing import Optional

import disnake
from disnake.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient

from assistant import Client
from config import mongo_uri


class LastSeen(commands.Cog):
    def __init__(self, client: Client):
        self.client = client
        self.mongo_db: Optional[AsyncIOMotorClient] = None

    async def update_time(self, user_id: int) -> None:
        if not self.mongo_db:
            self.mongo_db = self.client.connect_to_mongo()

        db = self.mongo_db["assistant"]
        collection = db["allUsers"]

        await collection.update_one({"_id": user_id},
                                    {"$set": {"lastSeen": int(datetime.datetime.now().timestamp())}},
                                    upsert=True)

    @commands.Cog.listener()
    async def on_presence_update(self, before: disnake.Member, after: disnake.Member) -> None:
        if before.bot:
            return
        if (before.raw_status == after.raw_status) or \
                before.raw_status != 'offline' and after.raw_status != 'offline':
            return
        await self.update_time(after.id)

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message) -> None:
        author = message.author
        if isinstance(author, disnake.User):
            return
        if author.bot:
            return
        if author.raw_status != 'offline':
            return
        await self.update_time(author.id)

    @commands.Cog.listener()
    async def on_typing(self, channel: disnake.TextChannel, user: disnake.Member, when: datetime) -> None:
        if isinstance(channel, disnake.DMChannel):
            return
        if user.bot:
            return
        if user.raw_status != 'offline':
            return
        await self.update_time(user.id)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: disnake.Member,
                                    before: disnake.VoiceState, after: disnake.VoiceState) -> None:
        if member.bot:
            return
        if member.raw_status != 'offline':
            return
        await self.update_time(member.id)

    @commands.Cog.listener()
    async def on_member_join(self, member: disnake.Member) -> None:
        if member.bot:
            return
        await self.update_time(member.id)


def setup(client: Client):
    if mongo_uri:
        client.add_cog(LastSeen(client))
    else:
        client.logger.warning("Database not configured, LastSeen cog will not be loaded.")
