# Imports
from os import getpid
from platform import python_version

import aiosqlite
import disnake
import lavalink
import psutil
from disnake import Embed
from disnake.ext import commands
from disnake.ext.commands import Param

import assistant
from EnvVariables import Owner_ID
from assistant import available_clients, time_delta, human_bytes, all_activities


class UserInfo(commands.Cog):
    def __init__(self, client: assistant.Client):
        self.client = client

    @commands.slash_command(description="Luk wat he be doing over der")
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def whois(self, inter: disnake.ApplicationCommandInteraction,
                    user: disnake.Member = Param(description="Mention a User",
                                                 default=lambda inter: inter.author), ) -> None:
        embed = await self.WhoIsEmbed(user)
        await inter.response.send_message(embed=embed)

    @commands.user_command(name="Who is this Guy?")
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def ContextWhoIs(self, inter: disnake.UserCommandInteraction) -> None:
        embed = await self.WhoIsEmbed(inter.target)
        await inter.response.send_message(embed=embed)

    async def WhoIsEmbed(self, user: disnake.Member) -> Embed:

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
        embed.add_field(name=f"Joined {user.guild.name} on",
                        value=f"{user.joined_at.strftime(date_format)} **{time_delta(user.joined_at)}**", )
        embed.add_field(name="Account created on",
                        value=f"{user.created_at.strftime(date_format)} **{time_delta(user.created_at)}**", )
        if user.nick is not None:
            embed.add_field(name="Nickname", value=user.nick)
        # Clients
        if user.raw_status != "offline":
            embed.add_field(name="Available Clients", value=available_clients(user))
        # Activity
        for key, value in all_activities(user, with_time=True).items():
            if value:
                embed.add_field(name=key, value=value)

        if len(user.roles) > 1:
            role_string = " ".join([role.mention for role in user.roles][1:])
            embed.add_field(name=f"Roles [{len(user.roles) - 1}]", value=role_string, inline=False)
        embed.set_footer(text=f"User ID: {user.id}")
        return embed

    @commands.slash_command(description="Shows the avatar of the user")
    async def avatar(self, inter: disnake.ApplicationCommandInteraction,
                     user: disnake.Member = Param(description="Mention a User",
                                                  default=lambda inter: inter.author), ) -> None:
        avatar = Embed(title=f"{user.display_name}'s Avatar 🖼", color=user.colour)
        avatar.set_image(url=user.display_avatar.url)
        await inter.response.send_message(embed=avatar)

    @commands.user_command(name="Avatar")
    async def ContextAvatar(self, inter: disnake.UserCommandInteraction) -> None:
        avatar = Embed(title=f"{inter.target.display_name}'s Avatar 🖼")
        avatar.set_image(url=inter.target.display_avatar.url)
        await inter.response.send_message(embed=avatar)

    @commands.slash_command(description="Shows Bot's Info")
    async def botinfo(self, inter: disnake.ApplicationCommandInteraction) -> None:
        user = self.client.user
        embed = Embed(color=0xFF0060, description=user.mention)
        embed.set_author(name=user, icon_url=user.avatar.url)
        embed.set_thumbnail(url=user.avatar.url)
        embed.add_field(name="Created by", value=f"<@{Owner_ID}>")
        embed.add_field(name="Created on", value="21 Mar 2021")
        embed.add_field(name="No. of Guilds", value=f"{len(self.client.guilds)}", inline=False)
        embed.add_field(name="No. of Users", value=f"{len(self.client.users)}", inline=False)
        embed.set_footer(text=f"User ID: {user.id}")
        await inter.response.send_message(embed=embed)

    @commands.slash_command(description="Shows Bot's Stats")
    async def stats(self, inter: disnake.ApplicationCommandInteraction) -> None:
        user = self.client.user
        embed = Embed(color=0xFF0060, description=user.mention)
        embed.add_field(name="Python Version", value=f"v. {python_version()}")
        used_memory = psutil.Process(getpid()).memory_info().rss
        embed.add_field(name="Python Memory Usage", value=f"{human_bytes(used_memory)}")
        embed.add_field(name=f"{disnake.__title__.capitalize()} Version",
                        value=f"v. {disnake.__version__}", inline=False)
        embed.add_field(name="Lavalink Version",
                        value=f"v. {lavalink.__version__}" if lavalink is not None else "Not Installed")
        lava_stats: lavalink.Stats = self.client.lavalink.node_manager.nodes[0].stats
        embed.add_field(name="Lavalink Memory Usage",
                        value=f"{human_bytes(lava_stats.memory_used)}/{human_bytes(lava_stats.memory_allocated)}")
        embed.add_field(name="System CPU Usage", value=f"{psutil.cpu_percent()}%", inline=False)
        embed.add_field(name="System Memory Usage",
                        value=f"{human_bytes(psutil.virtual_memory().used)}/{human_bytes(psutil.virtual_memory().total)}")
        embed.set_footer(text=f"User ID: {user.id}")
        await inter.response.send_message(embed=embed)

    @commands.slash_command(description="Introduce Yourself to Others.")
    async def introduce(self, inter: disnake.ApplicationCommandInteraction, ) -> None:
        class MyModal(disnake.ui.Modal):
            def __init__(self) -> None:
                components = [disnake.ui.TextInput(label="Introduce Yourself",
                                                   placeholder="I am a big pussy",
                                                   custom_id="content",
                                                   style=disnake.TextInputStyle.long,
                                                   min_length=5, max_length=512, ), ]

                super().__init__(title="Add Introduction", custom_id="add_intro", components=components)

            async def callback(self, _inter: disnake.ModalInteraction) -> None:
                await UserInfo.AddDatatoDB(user_id=inter.author.id,
                                           message=_inter.text_values['content'].replace('"', ''))
                await _inter.response.send_message("Introduction Added.", ephemeral=True)

            async def on_error(self, error: Exception, _inter: disnake.ModalInteraction) -> None:
                await _inter.response.send_message("Oops, something went wrong.", ephemeral=True)

        await inter.response.send_modal(modal=MyModal())

    async def AddDatatoDB(self, user_id: int, message: str) -> None:
        await self.client.log(f"Adding introduction for {user_id}: {message}")
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
