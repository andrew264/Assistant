from disnake.ext import commands

from assistant import Client


class Ready(commands.Cog):
    def __init__(self, client: Client):
        self.client = client

    @commands.Cog.listener("on_ready")
    async def after_start(self):
        self.client.logger.info("All cogs loaded.")
        self.client.logger.info(f"{self.client.user} is ready!")

    @commands.Cog.listener("on_ready")
    async def _remove_last_seen_from_db(self):
        """
        Removes the last_seen column from the database.
        """
        db = await self.client.db_connect()
        if db is None:
            self.client.logger.error("Failed to connect to database.")
            return
        await db.execute("UPDATE Members SET last_seen = NULL")
        await db.commit()
        self.client.logger.info("Removed last_seen column from database")

    @commands.Cog.listener()
    async def on_message(self, message):
        self.client.events['messages'] += 1

    @commands.Cog.listener()
    async def on_presence_update(self, before, after):
        self.client.events['presence_update'] += 1


def setup(client):
    client.add_cog(Ready(client))
