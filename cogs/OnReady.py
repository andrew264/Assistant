# Imports
import os
import platform

import disnake
from disnake.ext import commands

from EnvVariables import Owner_ID
from cogs.UserInfo import AvailableClients, timeDelta

old_str1 = ""


# Custom Act
def CustomActVal(activity: disnake.CustomActivity) -> str:
    value: str = "Status: "
    if activity.emoji is not None:
        value += str(activity.emoji)
    if activity.name is not None:
        value += activity.name
    return value


# Activities
def activity_string(member: disnake.Member):
    str1 = ""
    for activity in member.activities:
        if isinstance(activity, disnake.Spotify):
            str1 += f"\n\t\t\t> Listening to {activity.title} by {', '.join(activity.artists)} {timeDelta(activity.start)}"
        elif isinstance(activity, disnake.CustomActivity):
            str1 += f"\n\t\t\t> {CustomActVal(member.activity)} {timeDelta(activity.created_at)}"
        else:
            str1 += f"\n\t\t\t> Playing {activity.name} {timeDelta(activity.created_at)}"
    return str1


class Ready(commands.Cog):
    def __init__(self, client: disnake.Client):
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
        user = disnake.utils.get(self.client.get_all_members(), id=Owner_ID)
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

        # Print in Terminal
        await self.Output()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after) -> None:
        await self.Output()

    @commands.Cog.listener()
    async def on_presence_update(self, before, after) -> None:
        await self.Output()


def setup(client):
    client.add_cog(Ready(client))
