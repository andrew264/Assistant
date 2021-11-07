# Imports
import disnake
from disnake.ext import commands
from disnake import ApplicationCommandInteraction, Client, Embed, Member
from disnake.utils import find


class PrivateChat(commands.Cog):
    def __init__(self, client: Client):
        self.client = client

    # Create private category for DMs
    @commands.slash_command(description="Create a Private Chat & VC.")
    async def chat(self, inter: ApplicationCommandInteraction) -> None:
        pass

    @chat.sub_command(description="Create a new Private Chat.")
    async def create(self, inter: ApplicationCommandInteraction) -> None:
        overwrites_readEnable = disnake.PermissionOverwrite()
        overwrites_readEnable.read_messages = True
        for category in inter.guild.categories:
            if category.name == f"{inter.author.display_name}'s Chat" and isinstance(
                inter.author, Member
            ):
                for channel in category.channels:
                    await channel.set_permissions(
                        inter.author, overwrite=overwrites_readEnable
                    )
                await category.set_permissions(
                    inter.author, overwrite=overwrites_readEnable
                )
                return await inter.response.send_message(
                    f"Created a new Private Chat ({category.mention}).", ephemeral=True
                )
        daBotsRole = find(lambda r: r.id == 821762347659165727, inter.guild.roles)
        overwrites_readTrue = {
            inter.guild.default_role: disnake.PermissionOverwrite(read_messages=False),
            inter.guild.me: disnake.PermissionOverwrite(read_messages=True),
            inter.author: disnake.PermissionOverwrite(read_messages=True),
            daBotsRole: disnake.PermissionOverwrite(read_messages=True),
        }
        category: disnake.CategoryChannel = await inter.guild.create_category(
            f"{inter.author.display_name}'s Chat",
            overwrites=overwrites_readTrue,
            reason=None,
            position=None,
        )
        textChannel = await category.create_text_channel(
            "private-chat", overwrites=overwrites_readTrue
        )
        voiceChannel = await category.create_voice_channel(
            "Private Call Booth", overwrites=overwrites_readTrue
        )
        await inter.response.send_message(
            f"Created a new Private Chat ({category.mention}).", ephemeral=True
        )
        await voiceChannel.edit(rtc_region="india", bitrate=96000)
        embed = Embed(
            colour=0x002366,
            title=f"Welcome, {inter.author.display_name}!",
            description="This is a Private Chat.\nNo one else can see this channel other than us.\n:3",
        )
        await textChannel.send(embed=embed)

    @chat.sub_command(description="Delete existing Private Chat.")
    async def delete(self, inter: ApplicationCommandInteraction) -> None:
        overwrites_readFalse = disnake.PermissionOverwrite()
        overwrites_readFalse.read_messages = False
        category = None
        for i in inter.guild.categories:
            if i.name == f"{inter.author.display_name}'s Chat":
                category = i
            else:
                category = None
        if isinstance(category, disnake.CategoryChannel) and isinstance(
            inter.author, Member
        ):
            for channel in category.channels:
                await channel.set_permissions(
                    inter.author, overwrite=overwrites_readFalse
                )
            await category.set_permissions(inter.author, overwrite=overwrites_readFalse)
            return await inter.response.send_message(
                "Private Chat Deleted.", ephemeral=True
            )
        elif category is None:
            return await inter.response.send_message(
                "You don't have a Private Chat", ephemeral=True
            )


def setup(client):
    client.add_cog(PrivateChat(client))
