# Imports
import disnake
from disnake.ext import commands

from assistant import Client, colour_gen


class OnJoin(commands.Cog):
    def __init__(self, client: Client):
        self.client = client

    # Send DM on Member Join
    @commands.Cog.listener()
    async def on_member_join(self, member: disnake.Member) -> None:
        if member.guild.id == 368297437057515522:
            join_dm = disnake.Embed(title=f"Hey {member.name}!!!", colour=colour_gen(member.id), )
            join_dm.description = f"Welcome to \
            [{member.guild.name}](https://discord.com/channels/368297437057515522/844459471806791700)."
            join_dm.set_thumbnail(url=member.guild.icon.url)
            join_dm.add_field(name="\u200b",
                              value="""
                This Server is made by Gamers for Gamers.
                Make sure to respect each and every gamers and follow the rules.
                Check out Server Rules in [#rules](https://discord.com/channels/368297437057515522/830832846007828480).
                😀""", )
            try:
                await member.send(embed=join_dm)
                self.client.logger.info(f"Sent Welcome message to {member}")
            except disnake.Forbidden or disnake.HTTPException:
                self.client.logger.warning(f"Couldn't send Welcome message to {member}")
                pass


def setup(client):
    client.add_cog(OnJoin(client))
