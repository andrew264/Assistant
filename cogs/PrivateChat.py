# Imports
import disnake
from disnake.ext import commands
from disnake.utils import find

import assistant
from EnvVariables import HOMIES


class PrivateChat(commands.Cog):
    def __init__(self, client: assistant.Client):
        self.client = client

    # Create private category for DMs
    @commands.slash_command(description="Create a Private Chat & VC.", guild_ids=[HOMIES])
    @commands.guild_only()
    async def chat(self, inter: disnake.ApplicationCommandInteraction) -> None:
        pass

    @chat.sub_command(description="Create a new Private Chat.")
    async def create(self, inter: disnake.ApplicationCommandInteraction) -> None:
        for category in inter.guild.categories:
            if category.name == f"{inter.author.display_name}'s Chat" and isinstance(inter.author, disnake.Member):
                for channel in category.channels:
                    await channel.set_permissions(inter.author,
                                                  overwrite=disnake.PermissionOverwrite(read_messages=True))
                await category.set_permissions(inter.author, overwrite=disnake.PermissionOverwrite(read_messages=True))
                await inter.response.send_message(f"Created a new Private Chat ({category.mention}).", ephemeral=True)
                return
        overwrites_read = {
            inter.guild.default_role: disnake.PermissionOverwrite(read_messages=False),
            inter.guild.me: disnake.PermissionOverwrite(read_messages=True),
            inter.author: disnake.PermissionOverwrite(read_messages=True),
        }
        bots_role = find(lambda r: r.id == 821762347659165727, inter.guild.roles)
        if bots_role:
            overwrites_read[bots_role] = disnake.PermissionOverwrite(read_messages=True)
        category: disnake.CategoryChannel = await inter.guild.create_category(f"{inter.author.display_name}'s Chat",
                                                                              overwrites=overwrites_read,
                                                                              reason=None, )
        text = await category.create_text_channel("private-chat", overwrites=overwrites_read)
        voice = await category.create_voice_channel("Private Call Booth", overwrites=overwrites_read)
        await inter.response.send_message(f"Created a new Private Chat ({category.mention}).", ephemeral=True)
        await voice.edit(rtc_region=disnake.VoiceRegion.india, bitrate=96000)
        embed = disnake.Embed(colour=0x002366, title=f"Welcome, {inter.author.display_name}!",
                              description="""This is a Private Chat.No one else can see this channel other than us.\n:3""",
                              timestamp=disnake.utils.utcnow())
        await text.send(embed=embed)

    @chat.sub_command(description="Delete existing Private Chat.")
    async def delete(self, inter: disnake.ApplicationCommandInteraction) -> None:
        category = None
        for i in inter.guild.categories:
            if i.name == f"{inter.author.display_name}'s Chat":
                category = i
            else:
                category = None
        if isinstance(category, disnake.CategoryChannel) and isinstance(inter.author, disnake.Member):
            for channel in category.channels:
                await channel.set_permissions(inter.author, overwrite=disnake.PermissionOverwrite(read_messages=False))
            await category.set_permissions(inter.author, overwrite=disnake.PermissionOverwrite(read_messages=False))
            await inter.response.send_message("Private Chat Deleted.", ephemeral=True)
        elif category is None:
            await inter.response.send_message("You don't have a Private Chat", ephemeral=True)

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def purge_category(self, inter: disnake.ApplicationCommandInteraction) -> None:
        """delete all channels in the category"""
        await inter.response.send_message("Purging...")
        for category in inter.guild.categories:
            if category.id == inter.channel.category_id:
                for channel in category.channels:
                    await channel.delete()
        else:
            await inter.edit_original_message(content="Category not found.")


def setup(client):
    client.add_cog(PrivateChat(client))
