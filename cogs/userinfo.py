# Imports
from datetime import datetime, timezone
from platform import python_version

import aiosqlite
import disnake
from disnake import (
    Activity,
    ApplicationCommandInteraction,
    Client,
    CustomActivity,
    Embed,
    Game,
    Member,
    Spotify,
    Streaming,
    UserCommandInteraction,
)
from disnake.ext import commands
from disnake.ext.commands import Param


def ActivityVal(activity: Activity | Game) -> str:
    value: str = f"**{activity.name}**\n"
    if activity.start is not None:
        value += timeDelta(activity.start)
    return value


def timeDelta(timestamp: datetime) -> str:
    sec = (datetime.now(timezone.utc) - timestamp).seconds
    value: str = ""
    if sec < 60:
        value += f"({sec} s)"
    elif 60 <= sec < 3600:
        value += f"({sec // 60} mins {sec % 60} sec)"
    elif sec >= 3600:
        value += f"({sec // 3600} hrs {(sec // 60) % 60} mins)"
    return value


def CustomActVal(activity: CustomActivity) -> str:
    value: str = ""
    if activity.emoji is not None:
        value += f"[{activity.emoji}]({activity.emoji.url}) "
    if activity.name is not None:
        value += f"**{activity.name}**"
    value += f"\n{timeDelta(activity.created_at)}"
    return value


def AvailableClients(user: Member) -> str:
    clients = []
    if user.desktop_status.name != "offline":
        clients.append("Desktop")
    if user.mobile_status.name != "offline":
        clients.append("Mobile")
    if user.web_status.name != "offline":
        clients.append("Web")
    value = ', '.join(clients)
    if user.raw_status == "online":
        value = "Online in " + value
    elif user.raw_status == "idle":
        value = "Idling in " + value
    elif user.raw_status == "dnd":
        value = value + " (DND)"
    else:
        return "Offline"
    return value


class UserInfo(commands.Cog):
    def __init__(self, client: Client):
        self.client = client

    @commands.slash_command(description="Luk wat he be doing over der")
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def whois(self, inter: ApplicationCommandInteraction,
                    user: Member = Param(description="Mention a User", default=lambda inter: inter.author), ) -> None:
        embed = await self.WhoIsEmbed(user)
        await inter.response.send_message(embed=embed)

    @commands.user_command(name="Who is this Guy?")
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def ContextWhoIs(self, inter: UserCommandInteraction) -> None:
        embed = await self.WhoIsEmbed(inter.target)
        await inter.response.send_message(embed=embed)

    async def WhoIsEmbed(self, user: Member) -> Embed:

        date_format = "%a, %d %b %Y %I:%M %p"
        embed = Embed(color=user.colour)
        # Description
        about = await self.GetAboutfromDB(user.id)
        if about:
            embed.description = f"{user.mention}: {about}"
        else:
            embed.description = user.mention

        embed.set_author(name=user, icon_url=user.display_avatar.url)
        embed.set_thumbnail(url=user.display_avatar.url)
        time_now = datetime.now(timezone.utc)
        embed.add_field(name=f"Joined {user.guild.name} on",
                        value=f"""{user.joined_at.strftime(date_format)}
                        **({(time_now - user.joined_at).days} days ago)**""", )
        embed.add_field(name="Account created on",
                        value=f"""{user.created_at.strftime(date_format)}
                        **({(time_now - user.created_at).days} days ago)**""", )
        if user.nick is not None:
            embed.add_field(name="Nickname", value=user.nick)
        # Clients
        if user.raw_status != "offline":
            embed.add_field(name="Available Clients", value=AvailableClients(user))
        # Activity
        for activity in user.activities:
            if isinstance(activity, Game):
                embed.add_field(name="Playing", value=ActivityVal(activity))
            elif isinstance(activity, Streaming):
                embed.add_field(name=f"Streaming", value=f"[{activity.name}]({activity.url})")
            elif isinstance(activity, Spotify):
                embed.add_field(name="Spotify",
                                value=f"Listening to [{activity.title}]({activity.track_url} \"by {', '.join(activity.artists)}\")", )
                embed.set_thumbnail(url=activity.album_cover_url)
            elif isinstance(activity, CustomActivity):
                embed.add_field(name="Status", value=CustomActVal(activity))
            elif isinstance(activity, Activity):
                embed.add_field(name=f"{activity.type.name.capitalize()}", value=ActivityVal(activity), )
                if hasattr(activity, "large_image_url") and activity.large_image_url is not None:
                    embed.set_thumbnail(url=activity.large_image_url)
        if len(user.roles) > 1:
            role_string = " ".join([role.mention for role in user.roles][1:])
            embed.add_field(name=f"Roles [{len(user.roles) - 1}]", value=role_string, inline=False)
        embed.set_footer(text=f"User ID: {user.id}")
        return embed

    @commands.slash_command(description="Shows the avatar of the user")
    async def avatar(self, inter: ApplicationCommandInteraction,
                     user: Member = Param(description="Mention a User", default=lambda inter: inter.author), ) -> None:
        avatar = Embed(title=f"{user.display_name}'s Avatar 🖼", color=user.colour)
        avatar.set_image(url=user.display_avatar.url)
        await inter.response.send_message(embed=avatar)

    @commands.user_command(name="Avatar")
    async def ContextAvatar(self, inter: UserCommandInteraction) -> None:
        avatar = Embed(title=f"{inter.target.display_name}'s Avatar 🖼")
        avatar.set_image(url=inter.target.display_avatar.url)
        await inter.response.send_message(embed=avatar)

    @commands.slash_command(description="Shows Bot's Info")
    async def botinfo(self, inter: ApplicationCommandInteraction) -> None:
        user = self.client.user
        embed = Embed(color=0xFF0060, description=user.mention)
        embed.set_author(name=user, icon_url=user.avatar.url)
        embed.set_thumbnail(url=user.avatar.url)
        embed.add_field(name="Created by", value="Andrew", inline=False)
        embed.add_field(name="Created on", value="21 Mar 2021", inline=False)
        embed.add_field(name="Python Version", value=f"v. {python_version()}", inline=False)
        embed.add_field(name="Library Version", value=f"v. {disnake.__version__}", inline=False)
        embed.set_footer(text=f"User ID: {user.id}")
        return await inter.response.send_message(embed=embed)

    @commands.slash_command(description="Introduce Yourself to Others.")
    async def introduce(self, inter: ApplicationCommandInteraction,
                        message: str = Param(description="Enter a message"), ) -> None:
        await self.AddDatatoDB(user_id=inter.author.id, message=message.replace('"', ''))
        await inter.response.send_message("Introduction Added.")

    @staticmethod
    async def AddDatatoDB(user_id: int, message: str) -> None:
        async with aiosqlite.connect("./data/database.sqlite3") as db:
            async with db.execute(f"SELECT EXISTS(SELECT 1 FROM Members WHERE USERID = {user_id})") as cursor:
                alreadyExists = (await cursor.fetchone())[0]
                if alreadyExists:
                    await db.execute(f"""UPDATE Members SET ABOUT = "{message}" WHERE USERID = {user_id}""")
                else:
                    await db.execute(f"""INSERT INTO Members (USERID, ABOUT) VALUES ({user_id}, "{message}")""")
                assert db.total_changes > 0
                await db.commit()

    @staticmethod
    async def GetAboutfromDB(user_id: int) -> str | None:
        async with aiosqlite.connect("./data/database.sqlite3") as db:
            async with db.execute(f"SELECT EXISTS(SELECT 1 FROM Members WHERE USERID = {user_id})") as cursor:
                alreadyExists = (await cursor.fetchone())[0]
                if alreadyExists:
                    async with db.execute(f"SELECT * FROM Members WHERE USERID = {user_id}") as cursor1:
                        async for row in cursor1:
                            return row[1]
                else:
                    return None


def setup(client):
    client.add_cog(UserInfo(client))
