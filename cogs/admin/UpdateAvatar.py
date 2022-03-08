import io

import disnake
from disnake.ext import commands

from assistant import Client, colour_gen


class UpdateAvatar(commands.Cog):
    def __init__(self, client: Client):
        self.client = client

    @commands.slash_command(name="change_avatar", description="Change Bot's avatar", guild_ids=[821758346054467584])
    @commands.is_owner()
    async def client_avatar_update(self, inter: disnake.ApplicationCommandInteraction,
                                   avatar: disnake.Attachment = commands.Param(description="Avatar to change to")):
        """Update the bot's avatar"""
        await inter.response.defer()
        _avatar = io.BytesIO()
        await avatar.save(_avatar)
        await self.client.user.edit(avatar=_avatar.read())
        embed = disnake.Embed(title="Avatar Updated", colour=colour_gen(self.client.user.id))
        embed.set_author(name=self.client.user.name, icon_url=avatar.url)
        embed.set_image(url=avatar.url)
        await inter.edit_original_message(embed=embed)


def setup(client: Client):
    client.add_cog(UpdateAvatar(client))
