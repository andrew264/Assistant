import asyncio
import enum
from typing import Optional

import disnake
from disnake.ext import commands

from EnvVariables import HOMIES
from assistant import Client


class Choice(enum.Enum):
    NONE = 0
    rock = 1
    paper = 2
    scissors = 3


class RPSButtons(disnake.ui.View):
    def __init__(self, author: disnake.Member):
        super().__init__(timeout=30)
        self.choice: Choice = Choice.NONE
        self.selected = False
        self.author = author

    async def on_timeout(self) -> None:
        self.selected = True
        pass

    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        if interaction.author != self.author:
            await interaction.response.send_message("Start your OWN Game", ephemeral=True)
            return False
        return True

    @disnake.ui.button(emoji="🪨", label="Rock", style=disnake.ButtonStyle.gray)
    async def rock(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        button.style = disnake.ButtonStyle.green
        for _button in self.children:
            _button.disabled = True
        self.choice = Choice.rock
        self.selected = True
        await interaction.response.edit_message(content="You chose rock", view=self)

    @disnake.ui.button(emoji="📰", label="Paper", style=disnake.ButtonStyle.gray)
    async def paper(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        button.style = disnake.ButtonStyle.green
        for _button in self.children:
            _button.disabled = True
        self.choice = Choice.paper
        self.selected = True
        await interaction.response.edit_message(content="You chose paper", view=self)

    @disnake.ui.button(emoji="✂", label="Scissors", style=disnake.ButtonStyle.gray)
    async def scissors(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        button.style = disnake.ButtonStyle.green
        for _button in self.children:
            _button.disabled = True
        self.choice = Choice.scissors
        self.selected = True
        await interaction.response.edit_message(content="You chose scissors", view=self)


class RequestButtons(disnake.ui.View):
    def __init__(self, author: disnake.Member):
        super().__init__(timeout=30)
        self.author = author
        self.choice_view = RPSButtons(self.author)
        self.accepted: Optional[bool] = None

    async def on_timeout(self) -> None:
        self.accepted = False
        self.stop()

    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        if interaction.author != self.author:
            await interaction.response.send_message("Start your OWN Game", ephemeral=True)
            return False
        return True

    @disnake.ui.button(label="Accept", emoji="✅", style=disnake.ButtonStyle.gray)
    async def accept(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        button.style = disnake.ButtonStyle.green
        for _button in self.children:
            _button.disabled = True
        self.accepted = True
        await interaction.response.edit_message(content="Accepted", view=self)
        await interaction.followup.send("Select one:", view=self.choice_view, ephemeral=True)

    @disnake.ui.button(label="Denied", emoji="❌", style=disnake.ButtonStyle.gray)
    async def deny(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        button.style = disnake.ButtonStyle.red
        for _button in self.children:
            _button.disabled = True
        self.accepted = False
        await interaction.response.edit_message(content="Denied", view=None)


class RPS(commands.Cog):
    def __init__(self, client: Client):
        self.client = client

    @commands.slash_command(name="rps", description="Play Rock Paper Scissors", guild_ids=[HOMIES])
    async def rockpaperscissor(self, inter: disnake.ApplicationCommandInteraction,
                               player: disnake.Member = commands.Param(description="The player to play against",
                                                                       default=None)):
        """
        Play rock paper scissors with another user
        """
        host = inter.author
        player = player if player else inter.me
        if host == player:
            await inter.response.send_message("You can't play against yourself")
            return

        host_view = RPSButtons(host)
        player_view = RequestButtons(player)

        await inter.response.send_message(f"Waiting for {player.mention} to Accept", view=player_view)

        while player_view.accepted is None:
            await asyncio.sleep(0.33)
        if player_view.accepted:
            await inter.edit_original_message(
                content=f"Rock Paper Scissor!\n{host.mention} vs. {player.mention}\nLets see who wins!", view=None)
            await inter.followup.send("Select one:", view=host_view, ephemeral=True)
        else:
            await inter.edit_original_message(
                content=f"{player.mention} failed to accept the Challenge.\nWhat a pussy !", view=None)
            return

        while True:
            if player_view.choice_view.selected and host_view.selected:
                # print(f"{host.name} chose {host_view.choice}")
                # print(f"{player.name} chose {player_view.choice_view.choice}")
                break
            else:
                await asyncio.sleep(0.33)

        if player_view.choice_view.choice == Choice.NONE:
            await inter.edit_original_message(content=f"{player.mention} Failed to choose one.", view=None)
            return
        elif host_view.choice == Choice.NONE:
            await inter.edit_original_message(content=f"{host.mention} Failed to choose one.", view=None)
            return
        if player_view.choice_view.choice == host_view.choice:
            await inter.edit_original_message(
                content=f"{host.mention} and {player.mention} both chose {host_view.choice.name.title()}\nIt's a tie!",
                view=None)
            return

        def embed(host_win: bool) -> disnake.Embed:
            emb = disnake.Embed(title=f"{host.name} Won!" if host_win else f"{player.name} Won!",
                                colour=disnake.Colour.green())
            emb.set_author(name=f"Rock Paper Scissors!",
                           icon_url=host.display_avatar.url if host_win else player.display_avatar.url)
            emb.description = f"{host.mention} chose {host_view.choice.name.title()}\n" \
                              f"{player.mention} chose {player_view.choice_view.choice.name.title()}"
            return emb

        match host_view.choice:
            case Choice.rock:
                match player_view.choice_view.choice:
                    case Choice.paper:
                        await inter.edit_original_message(embed=embed(False), view=None)
                    case Choice.scissors:
                        await inter.edit_original_message(embed=embed(True), view=None)
            case Choice.paper:
                match player_view.choice_view.choice:
                    case Choice.rock:
                        await inter.edit_original_message(embed=embed(True), view=None)
                    case Choice.scissors:
                        await inter.edit_original_message(embed=embed(False), view=None)
            case Choice.scissors:
                match player_view.choice_view.choice:
                    case Choice.rock:
                        await inter.edit_original_message(embed=embed(False), view=None)
                    case Choice.paper:
                        await inter.edit_original_message(embed=embed(True), view=None)


def setup(client: Client):
    client.add_cog(RPS(client))
