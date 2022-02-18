# Imports
from datetime import datetime
from typing import Tuple, Optional

import disnake
from disnake import (
    Colour,
    Embed,
)
from disnake.ext import commands

import assistant
from EnvVariables import Owner_ID, Log_Channel
from assistant import available_clients, all_activities, custom_activity


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
    def __init__(self, client: assistant.Client):
        self.client = client

    @property
    def log_channel(self):
        return self.client.get_channel(Log_Channel)

    @property
    def log_guild(self) -> Optional[disnake.Guild]:
        return self.log_channel.guild

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
        await self.log_channel.send(embed=embed, delete_after=600)

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
        await self.log_channel.send(embed=embed, delete_after=600)

    @commands.Cog.listener()
    async def on_member_update(self, before: disnake.Member, after: disnake.Member) -> None:
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
        await self.log_channel.send(embed=embed, delete_after=600)

    @commands.Cog.listener()
    async def on_user_update(self, before: disnake.User, after: disnake.User) -> None:
        member: Optional[disnake.Member] = self.log_guild.get_member(before.id)
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
        embed.add_field(name="Old Username", value=str(before), inline=False, )
        embed.add_field(name="New Username", value=str(after), inline=False, )
        embed.set_footer(text=f"{datetime.now().strftime('%I:%M %p, %d %b')}")
        await self.log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_presence_update(self, before: disnake.Member, after: disnake.Member) -> None:
        if before.guild is None or before.guild != self.log_guild:
            return
        if before.bot:
            return
        if before.id == Owner_ID:
            return
        embed = Embed(colour=Colour.gold())
        embed.set_author(name=f"{before.display_name}'s Presence update", icon_url=before.display_avatar.url, )
        if available_clients(before) != available_clients(after):
            embed.add_field(name=f"Client/Status", value=f"{available_clients(before)} ──> {available_clients(after)}",
                            inline=False, )
            if before.raw_status == "offline" or after.raw_status == "offline":
                await self.log_channel.send(embed=embed, delete_after=1200)
                return

        # Activities
        for b_key, b_value in all_activities(before).items():
            if b_key == "Spotify":
                continue
            for a_key, a_value in all_activities(after).items():
                if b_key == a_key and b_value != a_value:
                    if b_value and not a_value:
                        embed.add_field(name=f"Stopped: {b_key}", value=f"{b_value}", inline=False, )
                    elif not b_value and a_value:
                        embed.add_field(name=f"Started: {b_key}", value=f"{a_value}", inline=False, )
                    else:
                        embed.add_field(name=f"Changed: {b_key}", value=f"{b_value} ──> {a_value}", inline=False, )

        if len(embed.fields):
            await self.log_channel.send(embed=embed, delete_after=900)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: disnake.Member, before: disnake.VoiceState,
                                    after: disnake.VoiceState) -> None:
        if member.guild != self.log_guild:
            return
        if member.bot or member.id == Owner_ID:
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
                delete_after=600, )

    @commands.Cog.listener()
    async def on_typing(self, channel: disnake.TextChannel, user: disnake.Member, when: datetime) -> None:
        if isinstance(channel, disnake.DMChannel):
            return
        if channel.guild != self.log_guild:
            return
        if user.bot or user.id == Owner_ID:
            return
        await self.log_channel.send(f"{user.display_name} started typing in {channel.mention}", delete_after=120)


def setup(client):
    client.add_cog(Surveillance(client))
