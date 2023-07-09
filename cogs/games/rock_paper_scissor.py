import enum
import random
from typing import Optional, Union

import discord
from discord import app_commands
from discord.ext import commands

from assistant import AssistantBot


class Choice(enum.Enum):
    NONE = 0
    rock = 1
    paper = 2
    scissors = 3


class RPSButtons(discord.ui.View):
    def __init__(self, player_1: Union[discord.Member, discord.User], player_2: Union[discord.Member, discord.User]):
        super().__init__(timeout=30)
        self.choices: dict[Union[discord.Member, discord.User], Choice] = {player_1: Choice.NONE, player_2: Choice.NONE}
        self.player_1 = player_1
        self.player_2 = player_2
        if player_1.bot:
            self.choices[player_1] = random.choice([Choice.rock, Choice.paper, Choice.scissors])
        if player_2.bot:
            self.choices[player_2] = random.choice([Choice.rock, Choice.paper, Choice.scissors])

    @property
    def both_selected(self) -> bool:
        return self.choices[self.player_1] != Choice.NONE and self.choices[self.player_2] != Choice.NONE

    async def _show_winner(self, interaction: discord.Interaction):
        for button in self.children:
            assert isinstance(button, discord.ui.Button)
            for key, value in self.choices.items():
                if button.custom_id == value.name:
                    winner = self._get_winner()
                    if key == winner:
                        button.style = discord.ButtonStyle.green
                    elif winner is None:
                        button.style = discord.ButtonStyle.blurple
                    else:
                        button.style = discord.ButtonStyle.red
            button.disabled = True
        winner = self._get_winner()
        embed = discord.Embed(title=f"{winner.display_name} won!" if winner else "It's a tie!",
                              color=discord.Color.random())
        embed.add_field(name=self.player_1.display_name, value=self.choices[self.player_1].name.capitalize())
        embed.add_field(name=self.player_2.display_name, value=self.choices[self.player_2].name.capitalize())
        await interaction.response.edit_message(content=None, embed=embed, view=self)

    def _get_winner(self) -> Union[discord.Member, discord.User, None]:
        match = self.choices[self.player_1], self.choices[self.player_2]
        if match == (Choice.rock, Choice.scissors) or \
                match == (Choice.paper, Choice.rock) or \
                match == (Choice.scissors, Choice.paper):
            return self.player_1
        elif match == (Choice.scissors, Choice.rock) or \
                match == (Choice.rock, Choice.paper) or \
                match == (Choice.paper, Choice.scissors):
            return self.player_2
        return None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.player_1 and interaction.user != self.player_2:
            await interaction.response.send_message("Start your OWN Game", ephemeral=True)
            return False
        if interaction.user == self.player_1 and self.choices[self.player_1] != Choice.NONE:
            await interaction.response.send_message("You already selected", ephemeral=True)
            return False
        if interaction.user == self.player_2 and self.choices[self.player_2] != Choice.NONE:
            await interaction.response.send_message("You already selected", ephemeral=True)
            return False
        return True

    @discord.ui.button(emoji="🪨", label="Rock", style=discord.ButtonStyle.gray, custom_id="rock")
    async def rock(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.choices[interaction.user] = Choice.rock
        if not self.both_selected:
            content = f"{interaction.user.mention} selected"
            if interaction.user == self.player_1:
                content += f"\nWaiting for {self.player_2.mention} to select"
            else:
                content += f"\nWaiting for {self.player_1.mention} to select"
            await interaction.response.edit_message(content=content, view=self)
        else:
            await self._show_winner(interaction)

    @discord.ui.button(emoji="📰", label="Paper", style=discord.ButtonStyle.gray, custom_id="paper")
    async def paper(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.choices[interaction.user] = Choice.paper
        if not self.both_selected:
            content = f"{interaction.user.mention} selected"
            if interaction.user == self.player_1:
                content += f"\nWaiting for {self.player_2.mention} to select"
            else:
                content += f"\nWaiting for {self.player_1.mention} to select"
            await interaction.response.edit_message(content=content, view=self)
        else:
            await self._show_winner(interaction)

    @discord.ui.button(emoji="✂", label="Scissors", style=discord.ButtonStyle.gray, custom_id="scissors")
    async def scissors(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.choices[interaction.user] = Choice.scissors
        if not self.both_selected:
            content = f"{interaction.user.mention} selected"
            if interaction.user == self.player_1:
                content += f"\nWaiting for {self.player_2.mention} to select"
            else:
                content += f"\nWaiting for {self.player_1.mention} to select"
            await interaction.response.edit_message(content=content, view=self)
        else:
            await self._show_winner(interaction)


class RPS(commands.Cog):
    def __init__(self, bot: AssistantBot):
        self.bot = bot

    @commands.hybrid_command(name='rps', description="Play rock paper scissors with another user",
                             aliases=['rockpaperscissor'])
    @app_commands.rename(player_2='opponent')
    @app_commands.describe(player_2="The user you want to play against")
    async def rockpaperscissor(self, ctx: commands.Context, player_2: Optional[discord.Member]):
        """
        Play rock paper scissors with another user
        """
        player_1 = ctx.author
        player_2 = player_2 if player_2 else ctx.bot.user
        if player_1 == player_2:
            await ctx.send(content="You can't play against yourself")
            return

        host_view = RPSButtons(player_1, player_2)
        await ctx.send(content=f"{player_1.mention}/{player_2.mention} choose your weapon", view=host_view)


async def setup(bot: AssistantBot):
    await bot.add_cog(RPS(bot))
