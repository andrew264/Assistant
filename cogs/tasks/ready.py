from disnake.ext import commands

from assistant import Client


class Ready(commands.Cog):
    def __init__(self, client: Client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{self.client.user} is ready!')
        self.client.load_extensions("./cogs/music")


def setup(client):
    client.add_cog(Ready(client))
