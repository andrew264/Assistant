import random
from typing import Optional, Union

import discord
from discord import utils, app_commands
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient

from assistant import AssistantBot
from utils import available_clients, all_activities


class UserInfo(commands.Cog):
    def __init__(self, bot: AssistantBot):
        self.bot = bot
        self.mongo: Optional[AsyncIOMotorClient] = None  # type: ignore
        for command in self.build_context_menus():
            self.bot.tree.add_command(command)

    async def cog_unload(self):
        for command in self.build_context_menus():
            self.bot.tree.remove_command(command.name, type=command.type)

    def build_context_menus(self):
        return [
            app_commands.ContextMenu(
                name="Who is this cute fella?",
                callback=self.__get_userinfo,
            ),
        ]

    @staticmethod
    def _get_thumbnail(user: Union[discord.Member, discord.User]) -> str:
        if isinstance(user, discord.User):
            return user.display_avatar.url
        _url = []
        for activity in user.activities:
            if isinstance(activity, discord.CustomActivity):
                if activity.emoji and activity.emoji.is_custom_emoji():
                    _url.append(activity.emoji.url)
            elif isinstance(activity, discord.Spotify):
                _url.append(activity.album_cover_url)
            elif isinstance(activity, discord.Game) or isinstance(activity, discord.Streaming):
                continue
            else:
                if hasattr(activity, 'large_image_url'):
                    _url.append(activity.large_image_url)
                elif hasattr(activity, 'small_image_url'):
                    _url.append(activity.small_image_url)
        if not _url:
            return user.display_avatar.url
        return random.choice(_url)

    async def _get_user_data(self, user: Union[discord.Member, discord.User]) -> dict:
        if self.mongo is None:
            self.mongo = self.bot.connect_to_mongo()
            if self.mongo is None:
                self.bot.logger.warning("Failed to fetch user data. MongoDB not connected.")
                return {}
        db = self.mongo['assistant']
        collection = db['allUsers']
        result = await collection.find_one({'_id': user.id})
        return result if result else {}

    @commands.hybrid_command(name="userinfo", aliases=["user"], description="Get information about a user")
    @app_commands.describe(user="The user to get information about")
    async def user_info(self, ctx: commands.Context, user: Optional[discord.Member | discord.User] = None):
        if not user:
            user = ctx.author

        await ctx.defer()
        is_admin = ctx.author.guild_permissions.administrator if isinstance(ctx.author, discord.Member) else False
        embed = await self.embed_generator(user, is_admin)
        view = discord.ui.View(timeout=120)
        view.add_item(discord.ui.Button(label="View Avatar", url=user.display_avatar.url))

        await ctx.send(embed=embed, view=view)

    async def __get_userinfo(self, ctx: discord.Interaction, user: discord.Member):
        await ctx.response.defer(ephemeral=True)
        embed = await self.embed_generator(user, False)
        view = discord.ui.View(timeout=120)
        view.add_item(discord.ui.Button(label="View Avatar", url=user.display_avatar.url))

        await ctx.edit_original_response(embed=embed, view=view)

    async def embed_generator(self, user: Union[discord.Member, discord.User], is_admin: bool = False) -> discord.Embed:
        embed = discord.Embed(color=user.color)

        user_data = await self._get_user_data(user)
        about = user_data.get('about')
        timestamp = user_data.get('lastSeen')
        if about:
            embed.description = f"{user.mention}: {about}"
        else:
            embed.description = f"{user.mention}"

        embed.set_author(name=f"{user}", icon_url=user.display_avatar.url)
        embed.set_thumbnail(url=self._get_thumbnail(user))

        if isinstance(user, discord.Member) and user.joined_at:  # Guild Member
            guild = self.bot.get_guild(user.guild.id)
            assert guild is not None
            fuser = guild.get_member(user.id)
            assert fuser is not None
            is_owner: bool = (user.guild.owner == user) and (
                    (user.joined_at - user.guild.created_at).total_seconds() < 2)
            # Guild Join Date
            embed.add_field(name=f"Created {user.guild.name} on" if is_owner else f"Joined {user.guild.name} on",
                            value=f"{utils.format_dt(user.joined_at, 'F')}\n{utils.format_dt(user.joined_at, 'R')}", )
            # Account Creation Date
            embed.add_field(name="Account created on",
                            value=f"{utils.format_dt(user.created_at, 'F')}\n{utils.format_dt(user.created_at, 'R')}", )

            if user.nick is not None:  # Nickname
                embed.add_field(name="Nickname", value=user.nick)

            if fuser.raw_status != 'offline':  # Available Clients
                embed.add_field(name="Available Clients", value=available_clients(fuser))

            if is_admin and timestamp:  # Last Seen
                embed.add_field(name="Last Seen" if fuser.raw_status == discord.Status.offline else "Online for",
                                value=f"<t:{timestamp}:R>", )

            # Activities
            for act_type, act_name in all_activities(fuser, with_time=True, with_url=True, include_all_activities=True):
                if act_name:
                    embed.add_field(name=act_type, value=act_name)

            if len(user.roles) > 1:  # Roles
                role_string = " ".join([role.mention for role in user.roles][1:])
                embed.add_field(name=f"Roles [{len(user.roles) - 1}]", value=role_string, inline=False)

        embed.set_footer(text=f"ID: {user.id}")

        return embed


async def setup(bot: AssistantBot):
    await bot.add_cog(UserInfo(bot))
