import datetime
from typing import Optional

import aiosqlite
import disnake
from disnake.ext import commands

from assistant import Client


class LastSeen(commands.Cog):
    def __init__(self, client: Client):
        self.client = client
        self.db: Optional[aiosqlite.Connection] = None

    async def update_time(self, user_id: int) -> None:
        if self.db is None:
            self.db = await self.client.db_connect()
        timestamp = int(datetime.datetime.now().timestamp())
        async with self.db.execute(f"SELECT * FROM Members WHERE USERID = {user_id}") as cursor:
            value = await cursor.fetchone()
            if value:
                await self.db.execute(f"UPDATE Members SET last_seen = '{timestamp}' WHERE USERID = {user_id}")
            else:
                await self.db.execute("INSERT INTO Members (USERID, last_seen) VALUES (?,?)", (user_id, timestamp))
            if self.db.total_changes:
                await self.db.commit()

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
    client.add_cog(LastSeen(client))
