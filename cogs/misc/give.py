import disnake
from disnake.ext import commands

from assistant import Client


class GiveCommand(commands.Cog):
    def __init__(self, client: Client):
        self.client = client

    @commands.slash_command(name="give", description="Give a user an item", )
    async def give(self, inter: disnake.ApplicationCommandInteraction,
                   item: str = commands.Param(description="Name of the item"),
                   quantity: int = commands.Param(description="No. of Items", ge=1, default=1),
                   to: disnake.Member = commands.Param(description="Give it to",
                                                       default=None)) -> None:
        message = f"{inter.author.mention} gave {item}" if to else f"You got {item}"
        if quantity > 1:
            message += f" x{quantity}"
        if to and to != inter.author:
            message += f" to {to.mention}"
        message += "."

        await inter.response.send_message(message)


def setup(client):
    client.add_cog(GiveCommand(client))
