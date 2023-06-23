import random
from typing import Optional

import disnake
from disnake.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient

from assistant import Client, colour_gen, long_date, relative_time, available_clients, all_activities


class UserInfo(commands.Cog):
    def __init__(self, client: Client):
        self.client = client
        self.mongo_client: Optional[AsyncIOMotorClient] = None

    async def _get_user_data(self, user: disnake.Member) -> dict:
        if self.mongo_client is None:
            self.mongo_client = self.client.connect_to_mongo()
            if self.mongo_client is None:
                self.client.logger.warning("Failed to fetch user data. MongoDB not connected.")
                return {}
        db = self.mongo_client['assistant']
        collection = db['allUsers']
        result = await collection.find_one({'_id': user.id})
        return result if result else {}

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

    @commands.slash_command(description="View Info", name="userinfo")
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def userinfo_slash(self, inter: disnake.ApplicationCommandInteraction,
                             user: disnake.Member = commands.Param(description="Mention a User",
                                                                   default=lambda inter: inter.author), ) -> None:
        await inter.response.defer()
        userinfo_embed = self.userinfo_embed
        is_admin = inter.channel.permissions_for(inter.author).administrator

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
            async def select_user(self, select: disnake.ui.UserSelect, interaction: disnake.Interaction) -> None:
                selected_user: disnake.Member = select.values[0]
                await interaction.response.edit_message(embed=await userinfo_embed(selected_user, is_admin),
                                                        view=self)

        await inter.edit_original_message(embed=await userinfo_embed(user, is_admin), view=View())

    @commands.user_command(name="User Info")
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def userinfo_user(self, inter: disnake.UserCommandInteraction, ) -> None:
        await inter.response.defer(ephemeral=True)
        is_admin = inter.channel.permissions_for(inter.author).administrator
        await inter.edit_original_message(embed=await self.userinfo_embed(inter.target, is_admin))

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def whois(self, ctx: commands.Context, user: Optional[disnake.Member]) -> None:
        if user is None:
            user = ctx.author
        is_admin = ctx.channel.permissions_for(user).administrator
        embed = await self.userinfo_embed(user, is_admin)
        await ctx.send(embed=embed)

    async def userinfo_embed(self, user: disnake.Member, is_admin: bool) -> disnake.Embed:
        embed = disnake.Embed(colour=colour_gen(user.id))
        # fetch user data from db
        user_data = await self._get_user_data(user)
        about = user_data.get('about')
        timestamp = user_data.get('lastSeen')
        if about:
            embed.description = f"{user.mention}: {about}"
        else:
            embed.description = f"{user.mention}"

        embed.set_author(name=f"{user}", icon_url=user.display_avatar.url)
        embed.set_thumbnail(url=self._get_thumbnail(user))
        is_owner: bool = (user.guild.owner == user) and ((user.joined_at - user.guild.created_at).total_seconds() < 2)
        embed.add_field(name=f"Created {user.guild.name} on" if is_owner else f"Joined {user.guild.name} on",
                        value=f"{long_date(user.joined_at)}\n{relative_time(user.joined_at)}", )
        embed.add_field(name="Account created on",
                        value=f"{long_date(user.created_at)}\n{relative_time(user.created_at)}", )
        if user.nick is not None:
            embed.add_field(name="Nickname", value=user.nick)

        # Clients
        if user.raw_status != "offline":
            embed.add_field(name="Available Clients", value=available_clients(user))
        # Last Seen
        if is_admin and timestamp:
            embed.add_field(name="Last Seen" if user.raw_status == 'offline' else "Online for",
                            value=f"{relative_time(timestamp)}")
        # Activities
        for act_type, act_name in all_activities(user, with_time=True, with_url=True, include_all_activities=True):
            if act_name:
                embed.add_field(name=act_type, value=act_name)

        if len(user.roles) > 1:
            role_string = " ".join([role.mention for role in user.roles][1:])
            embed.add_field(name=f"Roles [{len(user.roles) - 1}]", value=role_string, inline=False)
        embed.set_footer(text=f"User ID: {user.id}")
        return embed


def setup(client: Client):
    client.add_cog(UserInfo(client))
