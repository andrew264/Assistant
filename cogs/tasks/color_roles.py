import discord
from discord import Button, ButtonStyle
from discord.ext import commands

from assistant import AssistantBot


class ColourButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.roles = {"assistant:red": 891766305470971984,
                      "assistant:blue": 891766503219798026,
                      "assistant:green": 891766413721759764,
                      "assistant:brown": 891782414412697600,
                      "assistant:orange": 891783123711455292,
                      "assistant:purple": 891782622374678658,
                      "assistant:yellow": 891782804008992848, }

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        for role in interaction.user.roles:
            if role.id in list(self.roles.values()):
                await interaction.user.remove_roles(role)
        return True

    @discord.ui.button(emoji="🟥", style=ButtonStyle.gray, custom_id="assistant:red", row=0)
    async def red(self, interaction: discord.Interaction, button: Button):
        role = discord.Object(id=self.roles["assistant:red"])
        await interaction.user.add_roles(role)
        await interaction.response.send_message("Role added.", ephemeral=True)

    @discord.ui.button(emoji="🟦", style=ButtonStyle.gray, custom_id="assistant:blue", row=0)
    async def blue(self, interaction: discord.Interaction, button: Button):
        role = discord.Object(id=self.roles["assistant:blue"])
        await interaction.user.add_roles(role)
        await interaction.response.send_message("Role added.", ephemeral=True)

    @discord.ui.button(emoji="🟩", style=ButtonStyle.gray, custom_id="assistant:green", row=0)
    async def green(self, interaction: discord.Interaction, button: Button):
        role = discord.Object(id=self.roles["assistant:green"])
        await interaction.user.add_roles(role)
        await interaction.response.send_message("Role added.", ephemeral=True)

    @discord.ui.button(emoji="🟫", style=ButtonStyle.gray, custom_id="assistant:brown", row=0)
    async def brown(self, interaction: discord.Interaction, button: Button):
        role = discord.Object(id=self.roles["assistant:brown"])
        await interaction.user.add_roles(role)
        await interaction.response.send_message("Role added.", ephemeral=True)

    @discord.ui.button(emoji="🟧", style=ButtonStyle.gray, custom_id="assistant:orange", row=1)
    async def orange(self, interaction: discord.Interaction, button: Button):
        role = discord.Object(id=self.roles["assistant:orange"])
        await interaction.user.add_roles(role)
        await interaction.response.send_message("Role added.", ephemeral=True)

    @discord.ui.button(emoji="🟪", style=ButtonStyle.gray, custom_id="assistant:purple", row=1)
    async def purple(self, interaction: discord.Interaction, button: Button):
        role = discord.Object(id=self.roles["assistant:purple"])
        await interaction.user.add_roles(role)
        await interaction.response.send_message("Role added.", ephemeral=True)

    @discord.ui.button(emoji="🟨", style=ButtonStyle.gray, custom_id="assistant:yellow", row=1)
    async def yellow(self, interaction: discord.Interaction, button: Button):
        role = discord.Object(id=self.roles["assistant:yellow"])
        await interaction.user.add_roles(role)
        await interaction.response.send_message("Role added.", ephemeral=True)


class ColorRoles(commands.Cog):
    def __init__(self, bot: AssistantBot) -> None:
        self.bot = bot
        self.views_loaded = False

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.views_loaded:
            self.bot.add_view(ColourButtons())
            self.bot.logger.info("[LOADED] ColorRoles view.")
            self.views_loaded = True

    @commands.command()
    @commands.is_owner()
    async def reaction_roles(self, ctx: commands.Context) -> None:
        await ctx.message.delete()
        embed = discord.Embed(title="Reaction Roles", colour=0xFFFFFF, description="Claim a colour of your choice!", )
        await ctx.send(embed=embed, view=ColourButtons())


async def setup(bot: AssistantBot):
    await bot.add_cog(ColorRoles(bot))
