import disnake
from disnake.ext import commands

from assistant import Client


class Notes(commands.Cog):
    def __init__(self, client: Client):
        self.client = client

    @commands.slash_command(description="Add notes for later reference.")
    async def note(self, inter: disnake.ApplicationCommandInteraction):
        """
        Add notes for later reference.
        """
        await inter.response.send_message("Not implemented yet.", ephimeral=True)


def setup(client):
    client.add_cog(Notes(client))
