import random
from typing import Optional

import aiosqlite
import disnake
from disnake.ext import commands

from assistant import Client, available_clients, all_activities, colour_gen, relative_time, long_date


class UserInfo(commands.Cog):
    def __init__(self, client: Client):
        self.client = client
        self.db: Optional[aiosqlite.Connection] = None

    @commands.slash_command(description="View Info", name="userinfo")
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def userinfo_slash(self, inter: disnake.ApplicationCommandInteraction,
                             user: disnake.Member = commands.Param(description="Mention a User",
                                                                   default=lambda inter: inter.author), ) -> None:
        await inter.response.defer()
        userinfo_embed = self.userinfo_embed

        is_admin: bool = inter.channel.permissions_for(inter.author).administrator

        class View(disnake.ui.View):
            def __init__(self):
                super().__init__(timeout=60)

            async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
                return True if interaction.user == inter.author else False

            async def on_timeout(self):
                try:
                    await inter.edit_original_message(view=None)
                except disnake.NotFound:
                    pass

            @disnake.ui.user_select(placeholder="Select a User", min_values=1, max_values=1)
            async def select_user(self, select: disnake.ui.Select, interaction: disnake.Interaction) -> None:
                selected_user: disnake.Member = select.values[0]
                await interaction.response.edit_message(embed=await userinfo_embed(selected_user, is_admin),
                                                        view=self)

        await inter.edit_original_message(embed=await self.userinfo_embed(user, is_admin),
                                          view=View())

    @commands.user_command(name="Who is this Guy?")
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def userinfo_context(self, inter: disnake.UserCommandInteraction) -> None:
        await inter.response.defer(ephemeral=True)
        is_admin: bool = inter.channel.permissions_for(inter.author).administrator
        embed = await self.userinfo_embed(inter.target, is_admin)
        await inter.edit_original_message(embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def whois(self, ctx: commands.Context, user: Optional[disnake.Member]) -> None:
        if user is None:
            user = ctx.author
        embed = await self.userinfo_embed(user)
        await ctx.send(embed=embed)

    async def userinfo_embed(self, user: disnake.Member, is_admin: bool = False) -> disnake.Embed:

        embed = disnake.Embed(color=colour_gen(user.id))
        # Description
        about, timestamp = await self._fetch_db(user.id)
        if about:
            embed.description = f"{user.mention}: {about}"
        else:
            embed.description = user.mention

        embed.set_author(name=user, icon_url=user.display_avatar.url)
        embed.set_thumbnail(url=self._get_thumbnail(user))
        is_owner: bool = (user.guild.owner == user) and ((user.joined_at - user.guild.created_at).total_seconds() < 2)
        embed.add_field(name=f"Created {user.guild.name} on" if is_owner else f"Joined {user.guild.name} on",
                        value=f"{long_date(user.joined_at)}\n{relative_time(user.joined_at)}", )
        embed.add_field(name="Account created on",
                        value=f"{long_date(user.created_at)}\n{relative_time(user.created_at)}", )
        if user.nick is not None:
            embed.add_field(name="Nickname", value=user.nick)

        # No. of Reports
        report_count: int = await self._fetch_report_count(user) if is_admin else 0
        if report_count:
            embed.add_field(name="Total Reports", value=str(report_count))

        # Clients
        if user.raw_status != "offline":
            embed.add_field(name="Available Clients", value=available_clients(user))
        # Last Seen
        if is_admin and timestamp:
            embed.add_field(name="Last Seen" if user.raw_status == 'offline' else "Online for",
                            value=f"{relative_time(timestamp)}")
        # Activities
        for act_type, act_name in all_activities(user, with_time=True, with_url=True):
            if act_name:
                embed.add_field(name=act_type, value=act_name)

        if len(user.roles) > 1:
            role_string = " ".join([role.mention for role in user.roles][1:])
            embed.add_field(name=f"Roles [{len(user.roles) - 1}]", value=role_string, inline=False)
        embed.set_footer(text=f"User ID: {user.id}")
        return embed

    async def _fetch_db(self, user_id: int) -> tuple[Optional[str], Optional[int]]:
        """
        Fetch the user's info from the database
        :param user_id: The user's ID
        :return: The user's description and the timestamp of the last time the user was online can be None
        """
        self.db = await self.client.db_connect()
        async with self.db.execute("SELECT * FROM Members WHERE USERID = ?", (user_id,)) as cursor:
            value = await cursor.fetchone()
            about: Optional[str] = value[1] if value else None
            timestamp: Optional[int] = value[2] if value else None
            return about, timestamp

    async def _fetch_report_count(self, user: disnake.Member) -> int:
        """
        Fetch the user's total report count from the database
        :param user: The user
        :return: The user's report count
        """
        self.db = await self.client.db_connect()
        async with self.db.execute("SELECT COUNT(*) FROM MEMBER_REPORTS WHERE accused_id = ? AND guild_id = ?",
                                   (user.id, user.guild.id,)) as cursor:
            value = await cursor.fetchone()
            return value[0]

    @staticmethod
    def _get_thumbnail(user: disnake.Member) -> str:
        _url = []
        for activity in user.activities:
            if isinstance(activity, disnake.CustomActivity):
                if activity.emoji and activity.emoji.is_custom_emoji():
                    _url.append(activity.emoji.url)
            elif isinstance(activity, disnake.Spotify):
                _url.append(activity.album_cover_url)
            else:
                if hasattr(activity, 'large_image_url'):
                    _url.append(activity.large_image_url)
                elif hasattr(activity, 'small_image_url'):
                    _url.append(activity.small_image_url)
        if not _url:
            return user.display_avatar.url
        return random.choice(_url)


def setup(client) -> None:
    client.add_cog(UserInfo(client))
