# Imports
from enum import Enum
from random import randint, choice

import disnake
from disnake.ext import commands
from disnake.ext.commands import Param

import assistant
from EnvVariables import Owner_ID
from assistant import colour_gen, getch_hook

FEMALE_ROLES = (789081456110075936, 838868317779394560, 956593551943278612)


def death_msg_gen(victim: str, killer: str) -> str:
    death_msgs: tuple = (
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
    )
    if randint(0, 6):
        return victim + choice(death_msgs) + killer
    else:
        return killer + choice(death_msgs) + victim


def pp_generator(user_id: int) -> str:
    special_characters = (Owner_ID,)
    if user_id in special_characters:
        return f'[8{"=" * randint(7, 12)}D]' + \
               '(https://www.youtube.com/watch?v=dQw4w9WgXcQ "Ran out of Tape while measuring")'
    else:
        return f"8{'=' * randint(0, 9)}D"


# Bam types
class BamTypes(Enum):
    Kick = 0
    Ban = 1
    Left = 2


class Fun(commands.Cog):
    def __init__(self, client: assistant.Client):
        self.client = client

    @commands.slash_command(description="Measure them PPs")
    @commands.guild_only()
    async def pp(self, inter: disnake.ApplicationCommandInteraction,
                 user: disnake.Member = Param(description="Mention a User",
                                              default=lambda inter: inter.author), ) -> None:
        is_female = any(role.id in FEMALE_ROLES for role in user.roles)
        pp_embed = disnake.Embed(colour=colour_gen(user.id))
        pp_embed.set_author(name=user, icon_url=user.display_avatar.url)
        if is_female:
            pp_embed.add_field(name="There is no sign of PP in here.", value="\u200b")
        elif user.bot:
            pp_embed.add_field(name="There is no sign of life in here.", value="\u200b")
        else:
            pp_embed.add_field(name=f"{user.display_name}'s PP:", value=pp_generator(user.id), )
        pp_embed.set_footer(text=f"Inspected by: {inter.author.display_name}")
        await inter.response.send_message(embed=pp_embed)

    @commands.slash_command(description="Delete their existence")
    @commands.guild_only()
    async def kill(self, inter: disnake.ApplicationCommandInteraction,
                   user: disnake.Member = Param(description="Mention a User", default=lambda inter: inter.author), ):
        if user is None or user == inter.author:
            await inter.response.send_message("Stop, Get some Help.")
            return
        kill_embed = disnake.Embed(colour=colour_gen(user.id))
        kill_embed.set_author(name=user, icon_url=user.display_avatar.url)
        if user.bot:
            kill_embed.add_field(name="You cannot attack my kind.", value="\u200b")
        else:
            kill_embed.add_field(name=death_msg_gen(user.display_name, inter.author.display_name), value="\u200b", )
        await inter.response.send_message(embed=kill_embed)

    @commands.slash_command(description="Bam a User from this server.")
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_webhooks=True)
    async def bam(self, inter: disnake.ApplicationCommandInteraction,
                  target: disnake.Member = Param(description="Mention a User to Ban"),
                  types: BamTypes = Param(description="Select Ban Type", default=2), ) -> None:

        # Interaction Response
        await inter.response.send_message("Done 😏", ephemeral=True)

        # Impersonate MEE6
        try:
            user: disnake.Member = await inter.guild.fetch_member(159985870458322944)
        except disnake.NotFound:
            user = inter.author

        # Fetch Webhook
        webhook = await getch_hook(inter.channel)

        # Reply Msg
        match types:
            case 0:
                response = f"**{str(target)}** was kicked from the server"
            case 1:
                response = f"**{str(target)}** was banned from the server"
            case _:
                response = f"**{str(target)}** just left the server"

        # Send Webhook
        await webhook.send(content=response, username=user.display_name, avatar_url=user.display_avatar.url)


def setup(client):
    client.add_cog(Fun(client))
