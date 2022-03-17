from typing import List

import disnake
from disnake.ext import commands

from assistant import Client


class TicTacToeButton(disnake.ui.Button["TicTacToe"]):
    def __init__(self, x: int, y: int):
        super().__init__(style=disnake.ButtonStyle.secondary, label="\u200b", row=y)
        self.x = x
        self.y = y

    async def callback(self, interaction: disnake.MessageInteraction):
        assert self.view is not None
        view: TicTacToe = self.view
        host = view.host
        opponent = view.opponent
        state = view.board[self.y][self.x]
        if state in (view.X, view.O):
            return

        if view.current_player == view.X and interaction.author == host:
            self.style = disnake.ButtonStyle.blurple
            self.emoji = "❌"
            self.disabled = True
            view.board[self.y][self.x] = view.X
            view.current_player = view.O
            content = f"It is now {opponent.mention}'s turn"
        elif view.current_player == view.O and interaction.author == opponent:
            if opponent.bot:
                pass  # this should be playable against bots some time in the future
            self.style = disnake.ButtonStyle.success
            self.emoji = "⭕"
            self.disabled = True
            view.board[self.y][self.x] = view.O
            view.current_player = view.X
            content = f"It is now {host.mention}'s turn"
        else:
            await interaction.response.send_message(content="Wait for your turn!", ephemeral=True)
            return  # Don't do anything else

        winner = view.check_board_winner()
        if winner is not None:
            if winner == view.X:
                content = f"{host.mention} won!"
            elif winner == view.O:
                content = f"{opponent.mention} won!"
            else:
                content = f"{host.mention} and {opponent.mention} tied!"

            for child in view.children:
                child.disabled = True

            view.stop()

        await interaction.response.edit_message(content=content, view=view)


# This is our actual board View
class TicTacToe(disnake.ui.View):
    children: List[TicTacToeButton]
    X: int = -1
    O: int = 1
    Tie: int = 2

    def __init__(self, host: disnake.Member, opponent: disnake.Member):
        super().__init__()
        self.current_player = self.X
        self.board = [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]
        self.host = host
        self.opponent = opponent

        # Our board is made up of 3 by 3 TicTacToeButtons
        for x in range(3):
            for y in range(3):
                self.add_item(TicTacToeButton(x, y))

    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        if interaction.author == self.host or interaction.author == self.opponent:
            return True
        await interaction.response.send_message("Start your OWN Game with `/tictactoe`", ephemeral=True)
        return False

    # This method checks for the board winner
    def check_board_winner(self):
        for across in self.board:
            value = sum(across)
            if value == 3:
                return self.O
            elif value == -3:
                return self.X

        # Check vertical
        for line in range(3):
            value = self.board[0][line] + self.board[1][line] + self.board[2][line]
            if value == 3:
                return self.O
            elif value == -3:
                return self.X

        # Check diagonals
        diagonal = self.board[0][2] + self.board[1][1] + self.board[2][0]
        if diagonal == 3:
            return self.O
        elif diagonal == -3:
            return self.X

        diagonal = self.board[0][0] + self.board[1][1] + self.board[2][2]
        if diagonal == 3:
            return self.O
        elif diagonal == -3:
            return self.X

        # If we're here, we need to check if a tie was made
        if all(i != 0 for row in self.board for i in row):
            return self.Tie

        return None


class TTT(commands.Cog):
    def __init__(self, client: Client):
        self.client = client

    @commands.slash_command(name="tictactoe", description="Play a game of Tic Tac Toe")
    @commands.guild_only()
    async def ttt(self, inter: disnake.ApplicationCommandInteraction,
                  opponent: disnake.Member = commands.Param(description="An opponent to play against")):
        host = inter.author

        if host == opponent:
            await inter.response.send_message("You can't play against yourself! duh")
            return
        if opponent.bot:
            await inter.response.send_message("You can't play against a bot!")
            return

        # Create a new TicTacToe board
        view = TicTacToe(host, opponent)
        await inter.response.send_message(content=f"It is now {host.mention}'s turn", view=view)


def setup(client: Client):
    client.add_cog(TTT(client))
