# Imports
import asyncio
import os
import platform
import traceback

from disnake import (
    Activity,
    ActivityType,
    ApplicationCommandInteraction,
    Client,
    Color,
    CustomActivity,
    Embed,
    Member,
    Spotify,
    Status,
)
from disnake.ext import commands
from disnake.utils import get

from EnvVariables import DM_Channel, Owner_ID
from cogs.UserInfo import AvailableClients, timeDelta

old_str1 = ""


def fancy_traceback(exc: Exception) -> str:
    text = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    return f"```py\n{text[-4086:]}\n```"


# Custom Act
def CustomActVal(activity: CustomActivity) -> str:
    value: str = "Status: "
    if activity.emoji is not None:
        value += str(activity.emoji)
    if activity.name is not None:
        value += activity.name
    return value


# Activities
def activity_string(member: Member):
    str1 = ""
    for activity in member.activities:
        if isinstance(activity, Spotify):
            str1 += f"\n\t\t\t> Listening to {activity.title} by {', '.join(activity.artists)} {timeDelta(activity.start)}"
        elif isinstance(activity, CustomActivity):
            str1 += f"\n\t\t\t> {CustomActVal(member.activity)} {timeDelta(activity.created_at)}"
        else:
            str1 += f"\n\t\t\t> Playing {activity.name} {timeDelta(activity.created_at)}"
    return str1


class Ready(commands.Cog):
    def __init__(self, client: Client):
        self.client = client

    # Update Printed Text
    async def Output(self) -> None:
        global old_str1
        str1 = self.print_stuff()
        if old_str1 == str1:
            return

        if platform.system() == "Windows":
            os.system("cls")
        else:
            os.system("clear")
        print(str1)
        old_str1 = str1

    # Print Text Generator
    def print_stuff(self) -> str:
        str1 = f"{self.client.user} is connected to the following guild:"
        for guild in self.client.guilds:
            str1 += f"\n\t{guild.name} (ID: {guild.id}) (Member Count: {guild.member_count})"
        str1 += f"\n\nClient Latency: {round(self.client.latency * 1000)}  ms"
        user = get(self.client.get_all_members(), id=Owner_ID)
        str1 += f"\n\t\t{str(user)} is {AvailableClients(user)}"
        str1 += f"{activity_string(user)}"
        str1 += "\n\nPeople in VC:\n"
        for guild in self.client.guilds:
            for vc in guild.voice_channels:
                if len(vc.members) == 1 and any(Owner_ID == member.id for member in vc.members):
                    continue
                if vc.members:
                    str1 += f"\t🔊 {vc.name}:\n"
                for member in vc.members:
                    str1 += f"\t\t{member.display_name}"
                    if member.voice.self_mute or member.voice.mute:
                        str1 += "🙊"
                    if member.voice.self_deaf or member.voice.deaf:
                        str1 += "🙉"
                    if member.voice.self_stream:
                        str1 += " is live 🔴"
                    if member.voice.self_video:
                        str1 += "📷"
                    str1 += activity_string(member)
                    str1 += f"\n\t\t\t> {AvailableClients(member)}\n"
        return str1

    # Start
    @commands.Cog.listener()
    async def on_ready(self) -> None:
        # Load Music Cogs
        self.client.load_extension("cogs.music.play")
        self.client.load_extension("cogs.music.commands")
        self.client.load_extension("cogs.music.nowplaying")
        self.client.load_extension("cogs.music.queue")
        self.client.load_extension("cogs.music.effects")

        # Set Bot Activity
        await self.client.change_presence(status=Status.online,
                                          activity=Activity(type=ActivityType.watching, name="yall Homies."), )
        # Print in Terminal
        await self.Output()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after) -> None:
        await self.Output()

    @commands.Cog.listener()
    async def on_presence_update(self, before, after) -> None:
        await self.Output()

    # Unknown commands
    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send(error, delete_after=60)
        elif isinstance(error, commands.NotOwner):
            await ctx.send("🚫 You can't do that.", delete_after=60)
        elif isinstance(error, commands.UserInputError):
            await ctx.send(f"Error: Invalid {error.args[0]} Argument.")
        elif isinstance(error, commands.CheckFailure):
            await ctx.send(f"***{error}***")
        else:
            await ctx.send(f"***{error}***")
            channel = self.client.get_channel(DM_Channel)
            embed = Embed(title=f"Command `{ctx.command}` failed due to `{error}`", description=fancy_traceback(error),
                          color=Color.red(), )
            await channel.send(embed=embed)

    # slash errors
    @commands.Cog.listener()
    async def on_slash_command_error(self, inter: ApplicationCommandInteraction, error: commands.CommandError) -> None:
        if isinstance(error, commands.NotOwner):
            await inter.response.send_message("🚫 You can't do that.", ephemeral=True)
        elif isinstance(error, commands.MissingPermissions) or isinstance(error, commands.BotMissingPermissions):
            await inter.response.send_message(error, ephemeral=True)
        else:
            channel = self.client.get_channel(DM_Channel)
            embed = Embed(title=f"Command `{inter.application_command.name}` failed due to `{error}`",
                          description=fancy_traceback(error), color=Color.red(), )
            await channel.send(embed=embed)

    # Message Context Error
    @commands.Cog.listener()
    async def on_message_command_error(self, inter: ApplicationCommandInteraction,
                                       error: commands.CommandError) -> None:
        if isinstance(error, commands.NotOwner):
            await inter.response.send_message("🚫 You can't do that.", ephemeral=True)
        elif isinstance(error, commands.MissingPermissions):
            await inter.response.send_message(error, ephemeral=True)
        else:
            channel = self.client.get_channel(DM_Channel)
            embed = Embed(title=f"Command `{inter.application_command.name}` failed due to `{error}`",
                          description=fancy_traceback(error), color=Color.red(), )
            await channel.send(embed=embed)

    # User Context Error
    @commands.Cog.listener()
    async def on_user_command_error(self, inter: ApplicationCommandInteraction, error: commands.CommandError) -> None:
        if isinstance(error, commands.NotOwner):
            await inter.response.send_message("🚫 You can't do that.", ephemeral=True)
        elif isinstance(error, commands.MissingPermissions):
            await inter.response.send_message(error, ephemeral=True)
        else:
            channel = self.client.get_channel(DM_Channel)
            embed = Embed(title=f"Command `{inter.application_command.name}` failed due to `{error}`",
                          description=fancy_traceback(error), color=Color.red(), )
            await channel.send(embed=embed)


def setup(client):
    client.add_cog(Ready(client))
