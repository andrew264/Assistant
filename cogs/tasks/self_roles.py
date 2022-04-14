# Imports
import disnake
from disnake import Button, ButtonStyle
from disnake.ext import commands

from assistant import Client


class ColourButtons(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.roles = {"assistant:red": 891766305470971984,
                      "assistant:blue": 891766503219798026,
                      "assistant:green": 891766413721759764,
                      "assistant:brown": 891782414412697600,
                      "assistant:orange": 891783123711455292,
                      "assistant:purple": 891782622374678658,
                      "assistant:yellow": 891782804008992848, }

    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        for role in interaction.author.roles:
            if role.id in list(self.roles.values()):
                await interaction.author.remove_roles(role)
        return True

    @disnake.ui.button(emoji="🟥", style=ButtonStyle.gray, custom_id="assistant:red", row=0)
    async def red(self, button: Button, interaction: disnake.Interaction):
        role = [role for role in interaction.guild.roles if role.id == self.roles["assistant:red"]][0]
        await interaction.author.add_roles(role)
        await interaction.response.send_message(f"{role.mention} added.", ephemeral=True)

    @disnake.ui.button(emoji="🟦", style=ButtonStyle.gray, custom_id="assistant:blue", row=0)
    async def blue(self, button: Button, interaction: disnake.Interaction):
        role = [role for role in interaction.guild.roles if role.id == self.roles["assistant:blue"]][0]
        await interaction.author.add_roles(role)
        await interaction.response.send_message(f"{role.mention} added.", ephemeral=True)

    @disnake.ui.button(emoji="🟩", style=ButtonStyle.gray, custom_id="assistant:green", row=0)
    async def green(self, button: Button, interaction: disnake.Interaction):
        role = [role for role in interaction.guild.roles if role.id == self.roles["assistant:green"]][0]
        await interaction.author.add_roles(role)
        await interaction.response.send_message(f"{role.mention} added.", ephemeral=True)

    @disnake.ui.button(emoji="🟫", style=ButtonStyle.gray, custom_id="assistant:brown", row=0)
    async def brown(self, button: Button, interaction: disnake.Interaction):
        role = [role for role in interaction.guild.roles if role.id == self.roles["assistant:brown"]][0]
        await interaction.author.add_roles(role)
        await interaction.response.send_message(f"{role.mention} added.", ephemeral=True)

    @disnake.ui.button(emoji="🟧", style=ButtonStyle.gray, custom_id="assistant:orange", row=1)
    async def orange(self, button: Button, interaction: disnake.Interaction):
        role = [role for role in interaction.guild.roles if role.id == self.roles["assistant:orange"]][0]
        await interaction.author.add_roles(role)
        await interaction.response.send_message(f"{role.mention} added.", ephemeral=True)

    @disnake.ui.button(emoji="🟪", style=ButtonStyle.gray, custom_id="assistant:purple", row=1)
    async def purple(self, button: Button, interaction: disnake.Interaction):
        role = [role for role in interaction.guild.roles if role.id == self.roles["assistant:purple"]][0]
        await interaction.author.add_roles(role)
        await interaction.response.send_message(f"{role.mention} added.", ephemeral=True)

    @disnake.ui.button(emoji="🟨", style=ButtonStyle.gray, custom_id="assistant:yellow", row=1)
    async def yellow(self, button: Button, interaction: disnake.Interaction):
        role = [role for role in interaction.guild.roles if role.id == self.roles["assistant:yellow"]][0]
        await interaction.author.add_roles(role)
        await interaction.response.send_message(f"{role.mention} added.", ephemeral=True)


class SelfRoles(commands.Cog):
    def __init__(self, client: Client) -> None:
        self.client = client
        self.views_loaded = False

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.views_loaded:
            self.client.add_view(ColourButtons())
            self.client.logger.info("Loaded Colour Buttons")
            self.views_loaded = True

    @commands.command()
    @commands.is_owner()
    async def reaction_roles(self, ctx: commands.Context) -> None:
        await ctx.message.delete()
        embed = disnake.Embed(title="Reaction Roles", colour=0xFFFFFF,
                              description="Claim a colour of your choice!", )
        await ctx.send(embed=embed, view=ColourButtons())


def setup(client):
    client.add_cog(SelfRoles(client))
