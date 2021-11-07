# Imports
from disnake.ext import commands
from disnake import (
    Activity,
    Client,
    Colour,
    CustomActivity,
    Embed,
    Game,
    Member,
    Message,
    Spotify,
    Streaming,
    TextChannel,
    User,
    VoiceState,
)
from disnake.activity import ActivityTypes

from datetime import datetime
from typing import Tuple

# ID Numbers
OWNERID = 493025015445454868
CHANNEL_ID = 891369472101863494


def AvailableClients(user: Member) -> str:
    clients = []
    if user.desktop_status.name != "offline":
        clients.append("Desktop")
    if user.mobile_status.name != "offline":
        clients.append("Mobile")
    if user.web_status.name != "offline":
        clients.append("Web")
    if clients == []:
        return "Offline"
    return f"{', '.join(clients)}"


def StatusUpdate(user: Member):
    if user.raw_status == "online":
        return "Online"
    elif user.raw_status == "idle":
        return "Idle"
    elif user.raw_status == "dnd":
        return "Do not Disturb"
    elif user.raw_status == "offline":
        return "Offline"


def CustomActVal(activity: CustomActivity) -> str:
    value: str = ""
    if activity.emoji is not None:
        value += f"[{activity.emoji}]({activity.emoji.url}) "
    if activity.name is not None:
        value += activity.name
    return value


def ActivityVal(activities: Tuple[ActivityTypes, ...] = tuple()) -> list:
    activitiesList = []
    for activity in activities:
        if isinstance(activity, Game):
            activitiesList.append(f"{activity.type.name.capitalize()} {activity.name}")
        elif isinstance(activity, Streaming):
            activitiesList.append(f"Streaming {activity.name}")
        elif isinstance(activity, Spotify):
            # we dont need spotify activities
            continue
        elif isinstance(activity, CustomActivity):
            # handle CustomActivity Seperately
            continue
        elif isinstance(activity, Activity):
            activitiesList.append(f"{activity.type.name.capitalize()} {activity.name}")
    return activitiesList


class Surveillance(commands.Cog):
    def __init__(self, client: Client):
        self.client = client

    @commands.Cog.listener()
    async def on_message_edit(self, before: Message, after: Message) -> None:
        if before.author.bot:
            return
        if before.author.id == OWNERID:
            return
        if before.clean_content == after.clean_content:
            return
        log_channel: TextChannel = self.client.get_channel(CHANNEL_ID)
        embed = Embed(colour=Colour.teal())
        embed.set_author(
            name=f"{before.author} edited a message in #{before.channel.name}",
            icon_url=before.author.display_avatar.url,
        )
        embed.add_field(
            name="Original Message", value=before.clean_content, inline=False
        )
        embed.add_field(name="Altered Message", value=after.clean_content, inline=False)
        embed.set_footer(text=f"{datetime.now().strftime('%I:%M %p, %d %b')}")
        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message: Message) -> None:
        if message.author.bot:
            return
        if message.author.id == OWNERID:
            return
        log_channel: TextChannel = self.client.get_channel(CHANNEL_ID)
        embed = Embed(colour=Colour.orange())
        embed.set_author(
            name=f"{message.author} deleted a message in #{message.channel.name}",
            icon_url=message.author.display_avatar.url,
        )
        embed.add_field(name="Message Content", value=message.content, inline=False)
        embed.set_footer(text=f"{datetime.now().strftime('%I:%M %p, %d %b')}")
        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, before: Member, after: Member) -> None:
        if before.bot:
            return
        if before.id == OWNERID:
            return
        if before.display_name == after.display_name:
            return
        log_channel: TextChannel = self.client.get_channel(CHANNEL_ID)
        embed = Embed(colour=Colour.dark_orange())
        embed.set_author(
            name=f"{before} updated their Nickname", icon_url=before.display_avatar.url
        )
        embed.add_field(name="Old Name", value=before.display_name, inline=False)
        embed.add_field(name="New Name", value=after.display_name, inline=False)
        embed.set_footer(text=f"{datetime.now().strftime('%I:%M %p, %d %b')}")
        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_user_update(self, before: User, after: User) -> None:
        if before.bot:
            return
        if before.id == OWNERID:
            return
        if before.name == after.name and before.discriminator == after.discriminator:
            return
        log_channel: TextChannel = self.client.get_channel(CHANNEL_ID)
        embed = Embed(colour=Colour.brand_green())
        embed.set_author(
            name=f"{before} updated their Username", icon_url=before.display_avatar.url
        )
        embed.add_field(
            name="Old Username",
            value=f"{before.name} #{before.discriminator}",
            inline=False,
        )
        embed.add_field(
            name="New Username",
            value=f"{after.name} #{after.discriminator}",
            inline=False,
        )
        embed.set_footer(text=f"{datetime.now().strftime('%I:%M %p, %d %b')}")
        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_presence_update(self, before: Member, after: Member) -> None:
        if before.bot:
            return
        if before.id == OWNERID:
            return
        log_channel: TextChannel = self.client.get_channel(CHANNEL_ID)
        delete_after = 300
        embed = Embed(colour=Colour.gold())
        embed.set_author(
            name=f"{before.display_name}'s Presence update",
            icon_url=before.display_avatar.url,
        )
        if StatusUpdate(before) != StatusUpdate(after):
            embed.add_field(
                name=f"Status Update",
                value=f"{StatusUpdate(before)} ──> {StatusUpdate(after)}",
            )
            if delete_after == 300:
                delete_after += 43200
        if AvailableClients(before) != AvailableClients(after):
            embed.add_field(
                name=f"Client Update",
                value=f"{AvailableClients(before)} ──> {AvailableClients(after)}",
                inline=False,
            )
            if delete_after == 300:
                delete_after += 86400

        # Custom Activity
        before_custom, after_custom = None, None
        for activity in before.activities:
            if isinstance(activity, CustomActivity):
                before_custom = activity
        for activity in after.activities:
            if isinstance(activity, CustomActivity):
                after_custom = activity
        if before_custom is None and isinstance(after_custom, CustomActivity):
            embed.add_field(
                name=f"Custom Status added",
                value=f"{CustomActVal(after_custom)}",
                inline=False,
            )
            if delete_after == 300:
                delete_after += 43200
        elif after_custom is None and isinstance(before_custom, CustomActivity):
            embed.add_field(
                name=f"Custom Status removed",
                value=f"{CustomActVal(before_custom)}",
                inline=False,
            )
        elif (
            before_custom is not None
            and after_custom is not None
            and CustomActVal(before_custom) != CustomActVal(after_custom)
        ):
            embed.add_field(
                name=f"Custom Status modified",
                value=f"{CustomActVal(before_custom)}\n──>\n{CustomActVal(after_custom)}",
                inline=False,
            )
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
                embed.add_field(
                    name=f"Activity Update",
                    value=f"Stoped: {before_activity}",
                    inline=False,
                )
                delete_after = 300
        if after_activities:
            for after_activity in after_activities:
                embed.add_field(
                    name=f"Activity Update",
                    value=f"Started: {after_activity}",
                    inline=False,
                )
                if delete_after == 300:
                    delete_after += 1800

        if len(embed.fields):
            await log_channel.send(embed=embed, delete_after=delete_after)

    @commands.Cog.listener()
    async def on_voice_state_update(
        self, member: Member, before: VoiceState, after: VoiceState
    ) -> None:
        if member.bot:
            return
        if after.channel == before.channel:
            return
        log_channel: TextChannel = self.client.get_channel(CHANNEL_ID)
        if after.channel is None:
            await log_channel.send(
                f"{member.display_name} left {before.channel.mention}", delete_after=900
            )
        if before.channel is None:
            await log_channel.send(
                f"{member.display_name} joined {after.channel.mention}",
                delete_after=900,
            )
        elif after.channel is not None and before.channel is not None:
            await log_channel.send(
                f"{member.display_name} moved to {after.channel.mention} from {before.channel.mention}",
                delete_after=900,
            )

    @commands.Cog.listener()
    async def on_typing(
        self, channel: TextChannel, user: Member, when: datetime
    ) -> None:
        if user.bot:
            return
        if user.id == OWNERID:
            return
        if channel.name != "general-shit" and channel.name != "private-chat":
            return
        log_channel: TextChannel = self.client.get_channel(CHANNEL_ID)
        await log_channel.send(
            f"{user.display_name} started typing in {channel.mention}", delete_after=120
        )


def setup(client):
    client.add_cog(Surveillance(client))
