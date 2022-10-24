from disnake.ext import commands

from assistant import Client


class Ready(commands.Cog):
    def __init__(self, client: Client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        if 'cogs.music.play' not in self.client.extensions:
            self.client.load_extensions("./cogs/music")
            self.client.logger.info("All cogs loaded.")
            self.client.logger.info(f"{self.client.user} is ready!")

    @commands.Cog.listener()
    async def on_message(self, message):
        self.client.events['messages'] += 1

    @commands.Cog.listener()
    async def on_presence_update(self, before, after):
        self.client.events['presence_update'] += 1


def setup(client):
    client.add_cog(Ready(client))
