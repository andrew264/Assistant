from datetime import timedelta
from typing import Optional

import aiosqlite
import disnake
from disnake.ext import commands

from assistant import Client, time_delta, available_clients, all_activities, colour_gen


class UserInfo(commands.Cog):
    def __init__(self, client: Client):
        self.client = client
        self.db: Optional[aiosqlite.Connection] = None

    @commands.slash_command(description="Luk wat he be doing over der")
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def whois(self, inter: disnake.ApplicationCommandInteraction,
                    user: disnake.Member = commands.Param(description="Mention a User",
                                                          default=lambda inter: inter.author), ) -> None:
        embed = await self.WhoIsEmbed(user)
        await inter.response.send_message(embed=embed)

    @commands.user_command(name="Who is this Guy?")
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def ContextWhoIs(self, inter: disnake.UserCommandInteraction) -> None:
        embed = await self.WhoIsEmbed(inter.target)
        await inter.response.send_message(embed=embed)

    async def WhoIsEmbed(self, user: disnake.Member) -> disnake.Embed:

        embed = disnake.Embed(color=colour_gen(user.id))
        # Description
        about = await self.fetch_description(user.id)
        if about:
            embed.description = f"{user.mention}: {about}"
        else:
            embed.description = user.mention

        embed.set_author(name=user, icon_url=user.display_avatar.url)
        embed.set_thumbnail(url=user.display_avatar.url)
        is_owner: bool = user.guild.owner == user and \
                         timedelta(seconds=0) <= (user.guild.created_at - user.joined_at) <= timedelta(seconds=1)
        embed.add_field(name=f"Created {user.guild.name} on" if is_owner else f"Joined {user.guild.name} on",
                        value=f"<t:{int(user.joined_at.timestamp())}:D>\n**{time_delta(user.joined_at)}**", )
        embed.add_field(name="Account created on",
                        value=f"<t:{int(user.created_at.timestamp())}:D>\n**{time_delta(user.created_at)}**", )
        if user.nick is not None:
            embed.add_field(name="Nickname", value=user.nick)
        # Clients
        if user.raw_status != "offline":
            embed.add_field(name="Available Clients", value=available_clients(user))
        # Activity
        for key, value in all_activities(user, with_time=True, with_url=True).items():
            if value:
                embed.add_field(name=key, value=value)

        if len(user.roles) > 1:
            role_string = " ".join([role.mention for role in user.roles][1:])
            embed.add_field(name=f"Roles [{len(user.roles) - 1}]", value=role_string, inline=False)
        embed.set_footer(text=f"User ID: {user.id}")
        return embed

    async def fetch_description(self, user_id: int) -> Optional[str]:
        self.db = await self.client.db_connect()
        async with self.db.execute(f"SELECT * FROM Members WHERE USERID = {user_id}") as cursor:
            value = await cursor.fetchone()
            return value[1] if value else None


def setup(client):
    client.add_cog(UserInfo(client))
