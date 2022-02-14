# Imports
from datetime import datetime
from typing import Tuple, Optional

import disnake
from disnake import (
    Colour,
    Embed,
    Member,
)
from disnake.ext import commands

from EnvVariables import Owner_ID, Log_Channel
from cogs.UserInfo import AvailableClients


def CustomActVal(activity: disnake.CustomActivity) -> str:
    value: str = ""
    if activity.emoji is not None:
        value += f"[{activity.emoji}]({activity.emoji.url}) "
    if activity.name is not None:
        value += activity.name
    return value


def ActivityVal(activities: Tuple[disnake.Activity | disnake.Game |
                                  disnake.CustomActivity | disnake.Streaming
                                  | disnake.Spotify, ...]) -> list:
    activitiesList = []
    for activity in activities:
        if isinstance(activity, disnake.Game):
            activitiesList.append(f"{activity.type.name.capitalize()} {activity.name}")
        elif isinstance(activity, disnake.Streaming):
            activitiesList.append(f"Streaming {activity.name}")
        elif isinstance(activity, disnake.Spotify):
            # we don't need spotify activities
            continue
        elif isinstance(activity, disnake.CustomActivity):
            # handle CustomActivity Separately
            continue
        elif isinstance(activity, disnake.Activity):
            activitiesList.append(f"{activity.type.name.capitalize()} {activity.name}")
    return activitiesList


class Surveillance(commands.Cog):
    def __init__(self, client: disnake.Client):
        self.client = client
        self.log_channel: Optional[disnake.TextChannel] = None
        self.log_guild: Optional[disnake.Guild] = None

    @commands.Cog.listener()
    async def on_ready(self):
        self.log_channel = self.client.get_channel(Log_Channel)
        self.log_guild = self.log_channel.guild

    @commands.Cog.listener()
    async def on_message_edit(self, before: disnake.Message, after: disnake.Message) -> None:
        if before.guild is None or before.guild != self.log_guild:
            return
        if before.author.bot:
            return
        if before.author.id == Owner_ID:
            return
        if before.clean_content == after.clean_content:
            return
        embed = Embed(colour=Colour.teal())
        embed.set_author(name=f"{before.author} edited a message in #{before.channel.name}",
                         icon_url=before.author.display_avatar.url, )
        embed.add_field(name="Original Message", value=before.clean_content, inline=False)
        embed.add_field(name="Altered Message", value=after.clean_content, inline=False)
        embed.set_footer(text=f"{datetime.now().strftime('%I:%M %p, %d %b')}")
        await self.log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message: disnake.Message) -> None:
        if message.guild is None or message.guild != self.log_guild:
            return
        if message.author.bot:
            return
        if message.author.id == Owner_ID:
            return
        embed = Embed(colour=Colour.orange())
        embed.set_author(name=f"{message.author} deleted a message in #{message.channel.name}",
                         icon_url=message.author.display_avatar.url, )
        embed.add_field(name="Message Content", value=message.content, inline=False)
        embed.set_footer(text=f"{datetime.now().strftime('%I:%M %p, %d %b')}")
        await self.log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, before: Member, after: Member) -> None:
        if before.guild is None or before.guild != self.log_guild:
            return
        if before.bot:
            return
        if before.id == Owner_ID:
            return
        if before.display_name == after.display_name:
            return
        embed = Embed(colour=Colour.dark_orange())
        embed.set_author(name=f"{before} updated their Nickname", icon_url=before.display_avatar.url)
        embed.add_field(name="Old Name", value=before.display_name, inline=False)
        embed.add_field(name="New Name", value=after.display_name, inline=False)
        embed.set_footer(text=f"{datetime.now().strftime('%I:%M %p, %d %b')}")
        await self.log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_user_update(self, before: disnake.User, after: disnake.User) -> None:
        member: Optional[Member] = self.log_guild.get_member(before.id)
        if member is None:
            return
        if before.bot:
            return
        if before.id == Owner_ID:
            return
        if before.name == after.name and before.discriminator == after.discriminator:
            return
        embed = Embed(colour=Colour.brand_green())
        embed.set_author(name=f"{before} updated their Username", icon_url=before.display_avatar.url)
        embed.add_field(name="Old Username", value=f"{before.name} #{before.discriminator}", inline=False, )
        embed.add_field(name="New Username", value=f"{after.name} #{after.discriminator}", inline=False, )
        embed.set_footer(text=f"{datetime.now().strftime('%I:%M %p, %d %b')}")
        await self.log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_presence_update(self, before: Member, after: Member) -> None:
        if before.guild is None or before.guild != self.log_guild:
            return
        if before.bot:
            return
        if before.id == Owner_ID:
            return
        delete_after = 300
        embed = Embed(colour=Colour.gold())
        embed.set_author(name=f"{before.display_name}'s Presence update", icon_url=before.display_avatar.url, )
        if AvailableClients(before) != AvailableClients(after):
            embed.add_field(name=f"Client/Status", value=f"{AvailableClients(before)} ──> {AvailableClients(after)}",
                            inline=False, )
            if delete_after == 300:
                delete_after += 86400

        # Custom Activity
        before_custom, after_custom = None, None
        for activity in before.activities:
            if isinstance(activity, disnake.CustomActivity):
                before_custom = activity
        for activity in after.activities:
            if isinstance(activity, disnake.CustomActivity):
                after_custom = activity
        if before_custom is None and isinstance(after_custom, disnake.CustomActivity):
            embed.add_field(name=f"Custom Status added", value=f"{CustomActVal(after_custom)}", inline=False, )
            if delete_after == 300:
                delete_after += 43200
        elif after_custom is None and isinstance(before_custom, disnake.CustomActivity):
            embed.add_field(name=f"Custom Status removed", value=f"{CustomActVal(before_custom)}", inline=False, )
        elif (
                before_custom is not None
                and after_custom is not None
                and CustomActVal(before_custom) != CustomActVal(after_custom)
        ):
            embed.add_field(name=f"Custom Status modified",
                            value=f"{CustomActVal(before_custom)}\n──>\n{CustomActVal(after_custom)}", inline=False, )
            if delete_after == 300:
                delete_after += 43200

        # Other Activities
        before_activities = ActivityVal(before.activities)
        after_activities = ActivityVal(after.activities)
        for before_activity in before_activities:
            for after_activity in after_activities:
                if before_activity == after_activity:
                    before_activities.remove(before_activity)
                    after_activities.remove(after_activity)
        if before_activities:
            for before_activity in before_activities:
                embed.add_field(name=f"Activity Update", value=f"Stopped: {before_activity}", inline=False, )
                delete_after = 300
        if after_activities:
            for after_activity in after_activities:
                embed.add_field(name=f"Activity Update", value=f"Started: {after_activity}", inline=False, )
                if delete_after == 300:
                    delete_after += 1800

        if len(embed.fields):
            await self.log_channel.send(embed=embed, delete_after=delete_after)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: Member, before: disnake.VoiceState,
                                    after: disnake.VoiceState) -> None:
        if member.guild is None or member.guild != self.log_guild:
            return
        if member.bot:
            return
        if after.channel == before.channel:
            return
        if after.channel is None:
            await self.log_channel.send(f"{member.display_name} left {before.channel.mention}", delete_after=900)
        if before.channel is None:
            await self.log_channel.send(f"{member.display_name} joined {after.channel.mention}", delete_after=900, )
        elif after.channel is not None and before.channel is not None:
            await self.log_channel.send(
                f"{member.display_name} moved to {after.channel.mention} from {before.channel.mention}",
                delete_after=900, )

    @commands.Cog.listener()
    async def on_typing(self, channel: disnake.TextChannel, user: Member, when: datetime) -> None:
        if isinstance(channel, disnake.DMChannel):
            return
        if channel.guild is None or channel.guild != self.log_guild:
            return
        if user.bot:
            return
        if user.id == Owner_ID:
            return
        if channel.name != "general-shit" and channel.name != "private-chat":
            return
        await self.log_channel.send(f"{user.display_name} started typing in {channel.mention}", delete_after=120)


def setup(client):
    client.add_cog(Surveillance(client))
