from disnake.ext import commands

from assistant import Client


class LastSeen(commands.Cog):
    def __init__(self, client: Client):
        self.client = client


def setup(client: Client):
    client.add_cog(LastSeen(client))
