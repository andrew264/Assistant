# Imports
from random import randint, choice

import disnake
from disnake import Embed
from disnake.ext import commands
from disnake.ext.commands import Param
from disnake.utils import find


def DeathMsgGen(victim: str, killer: str) -> str:
    death_msgs: list[str] = [
        " was shot by ",
        " drowned whilst trying to escape ",
        " was blown up by ",
        " was killed by ",
        " walked into fire whilst fighting ",
        " was struck by lightning whilst fighting ",
        " was frozen to death by ",
        " was slain by ",
        " was squashed by ",
        " was killed trying to hurt ",
        " didn't want to live in the same world as ",
        " died because of ",
        " was doomed to fall by ",
        " got finished off by ",
        " was drowned by ",
    ]
    if randint(0, 6):
        return victim + choice(death_msgs) + killer
    else:
        return killer + choice(death_msgs) + victim


class Fun(commands.Cog):
    def __init__(self, client: disnake.Client):
        self.client = client

    @commands.slash_command(description="Measure them PPs")
    @commands.guild_only()
    async def pp(self, inter: disnake.ApplicationCommandInteraction,
                 user: disnake.Member = Param(description="Mention a User",
                                              default=lambda inter: inter.author), ) -> None:
        pp404 = find(lambda r: r.id == 838868317779394560, user.roles)
        ppembed = Embed(colour=user.color)
        ppembed.set_author(name=user, icon_url=user.display_avatar.url)
        if pp404 is not None:
            ppembed.add_field(name="There is no sign of PP in here.", value="\u200b")
        elif user.bot:
            ppembed.add_field(name="There is no sign of life in here.", value="\u200b")
        else:
            ppembed.add_field(name=f"{user.display_name}'s PP:", value=f"8{'=' * randint(0, 9)}D")
        ppembed.set_footer(text=f"Inspected by: {inter.author.display_name}")
        await inter.response.send_message(embed=ppembed)

    @commands.slash_command(description="Delete their existence")
    @commands.guild_only()
    async def kill(self, inter: disnake.ApplicationCommandInteraction,
                   user: disnake.Member = Param(description="Mention a User", default=lambda inter: inter.author), ):
        if user is None or user == inter.author:
            await inter.response.send_message("Stop, Get some Help.")
            return
        killembed = Embed(colour=user.color)
        killembed.set_author(name=user, icon_url=user.display_avatar.url)
        if user.bot:
            killembed.add_field(name="You cannot attack my kind.", value="\u200b")
        else:
            killembed.add_field(name=DeathMsgGen(user.display_name, inter.author.display_name), value="\u200b", )
        await inter.response.send_message(embed=killembed)


def setup(client):
    client.add_cog(Fun(client))
