import disnake
from disnake.ext import commands

from assistant import Client, colour_gen, to_file


class Avatar(commands.Cog):
    def __init__(self, client: Client):
        self.client = client

    @commands.slash_command(description="Shows the avatar of the user")
    async def avatar(self, inter: disnake.ApplicationCommandInteraction,
                     user: disnake.Member = commands.Param(description="Mention a User",
                                                           default=lambda inter: inter.author), ) -> None:
        await inter.response.defer()
        avatar = disnake.Embed(title=f"{user.display_name}'s Avatar 🖼", color=colour_gen(user.id))
        avatar.set_image(file=await to_file(user.display_avatar))
        await inter.edit_original_message(embed=avatar)

    @commands.user_command(name="Avatar")
    async def context_avatar(self, inter: disnake.UserCommandInteraction) -> None:
        await inter.response.defer(ephemeral=True)
        avatar = disnake.Embed(title=f"{inter.target.display_name}'s Avatar 🖼", color=colour_gen(inter.target.id))
        avatar.set_image(url=inter.target.display_avatar.url)
        await inter.edit_original_message(embed=avatar)


def setup(client):
    client.add_cog(Avatar(client))
