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

    @commands.Cog.listener()
    async def on_presence_update(self, before: disnake.Member, after: disnake.Member) -> None:
        if before.bot:
            return
        if (before.raw_status == after.raw_status) or \
                before.raw_status != 'offline' and after.raw_status != 'offline':
            return
        if self.db is None:
            self.db = await self.client.db_connect()
        user_id = before.id
        timestamp = int(datetime.datetime.now().timestamp())
        async with self.db.execute(f"SELECT * FROM Members WHERE USERID = {user_id}") as cursor:
            value = await cursor.fetchone()
            if value:
                await self.db.execute(f"UPDATE Members SET last_seen = '{timestamp}' WHERE USERID = {user_id}")
            else:
                await self.db.execute("INSERT INTO Members (USERID, last_seen) VALUES (?,?)", (user_id, timestamp))
            if self.db.total_changes:
                await self.db.commit()


def setup(client: Client):
    client.add_cog(LastSeen(client))
