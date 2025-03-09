import datetime

import discord
from discord.ext import commands

from assistant import AssistantBot
from config import DATABASE_NAME, MONGO_URI


class LastSeen(commands.Cog):
    def __init__(self, bot: AssistantBot):
        self.bot = bot

    async def update_time(self, user_id: int) -> None:
        db = self.bot.database[DATABASE_NAME]
        collection = db["allUsers"]

        await collection.update_one({"_id": user_id}, {"$set": {"lastSeen": int(datetime.datetime.now().timestamp())}}, upsert=True)

    @commands.Cog.listener('on_ready')
    async def reset_last_seen(self) -> None:
        db = self.bot.database[DATABASE_NAME]
        collection = db["allUsers"]
        await collection.update_many({}, {"$unset": {"lastSeen": ""}})
        self.bot.logger.info("[RESET] lastSeen times from DB.")

    @commands.Cog.listener()
    async def on_presence_update(self, before: discord.Member, after: discord.Member) -> None:
        if before.bot:
            return
        if (before.raw_status == after.raw_status) or before.raw_status != 'offline' and after.raw_status != 'offline':
            return
        await self.update_time(after.id)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        author = message.author
        if isinstance(author, discord.User):
            return
        if author.bot:
            return
        if author.raw_status != 'offline':
            return
        await self.update_time(author.id)

    @commands.Cog.listener()
    async def on_typing(self, channel: discord.TextChannel, user: discord.Member, when: datetime.datetime) -> None:
        if isinstance(channel, discord.DMChannel):
            return
        if user.bot:
            return
        if user.raw_status != 'offline':
            return
        await self.update_time(user.id)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState) -> None:
        if member.bot:
            return
        if member.raw_status != 'offline':
            return
        await self.update_time(member.id)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        if member.bot:
            return
        await self.update_time(member.id)


async def setup(bot: AssistantBot):
    if MONGO_URI:
        await bot.add_cog(LastSeen(bot))
    else:
        bot.logger.warning("[FAILED] last_seen.py cog not loaded. MONGO_URI not set.")
