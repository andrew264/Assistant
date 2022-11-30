import asyncio
import random
from math import inf
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
        if view.board[self.y][self.x] in (view.X, view.O):  # if the cell is occupied already
            return

        if view.current_player == view.X and interaction.author == host:
            view.update_board(self.y, self.x, view.X)
            view.current_player = view.O
            if opponent.bot:
                await interaction.response.edit_message(view=view)  # update the message quickly to show the move
                # make move in executor because it's blocking
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self.make_a_move)
                content = f"It is now {host.mention}'s turn"
                view.current_player = view.X
            else:
                await interaction.response.defer()
                content = f"It is now {opponent.mention}'s turn"
        elif view.current_player == view.O and interaction.author == opponent:
            await interaction.response.defer()
            view.update_board(self.y, self.x, view.O)
            view.current_player = view.X
            content = f"It is now {host.mention}'s turn"
        else:
            await interaction.response.send_message(content="Wait for your turn!", ephemeral=True)
            return  # Don't do anything else

        match view.check_board_winner():
            case view.X:
                content = f"{host.mention} won!"
            case view.O:
                content = f"{opponent.mention} won!"
            case 2:
                content = f"{host.mention} and {opponent.mention} tied!"
            case None:
                pass

        if view.check_board_winner() is not None:
            for child in view.children:
                child.disabled = True

            view.stop()

        await interaction.edit_original_message(content=content, view=view)

    def make_a_move(self):
        view = self.view
        depth = len(self.empty_cells())
        if depth == 0 or view.check_board_winner() is not None:
            return
        if depth == 9:
            x = random.randint(0, 2)
            y = random.randint(0, 2)
        else:
            move = self.minimax(depth, view.O)
            x, y = move[0], move[1]
        view.update_board(x, y, view.O)

    def empty_cells(self):
        """
        Each empty cell will be added into cells' list
        :return: a list of empty cells
        """
        cells = []

        for x, row in enumerate(self.view.board):
            for y, cell in enumerate(row):
                if cell == 0:
                    cells.append([x, y])
        return cells

    def minimax(self, depth, player):
        """
        AI function that choice the best move
        :param depth: node index in the tree (0 <= depth <= 9)
        :param player: a human or a computer
        :return: a list with [the best row, the best col, best score]
        """
        view: TicTacToe = self.view
        best = [-1, -1, -inf] if player == view.O else [-1, -1, +inf]

        if depth == 0 or view.check_board_winner() is not None:
            score = view.check_board_winner()
            return [-1, -1, score]

        for cell in self.empty_cells():
            x, y = cell[0], cell[1]
            view.board[x][y] = player
            score = self.minimax(depth - 1, -player)
            view.board[x][y] = 0
            score[0], score[1] = x, y

            if player == view.O:
                if score[2] > best[2]:
                    best = score  # max value
            else:
                if score[2] < best[2]:
                    best = score  # min value

        return best

    def print_board(self):
        print("-------------")
        for row in self.view.board:
            print("|", end=" ")
            for cell in row:
                if cell == self.view.X:
                    print("X", end=" | ")
                elif cell == self.view.O:
                    print("O", end=" | ")
                else:
                    print(" ", end=" | ")
            print("\n-------------")


# This is our actual board View
class TicTacToe(disnake.ui.View):
    children: List[TicTacToeButton]
    X: int = -1
    O: int = 1
    Tie: int = 2

    def __init__(self, host: disnake.Member, opponent: disnake.Member):
        super().__init__()
        self.current_player = self.X
        self._board = [
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

    @property
    def board(self) -> List[List[int]]:
        return self._board

    @board.setter
    def board(self, value: List[List[int]]):
        self._board = value

    def update_board(self, x: int, y: int, value: int):
        self._board[x][y] = value
        for child in self.children:
            if child.x == y and child.y == x:
                child.disabled = True
                child.value = value
                if value == self.X:
                    child.emoji = "❌"
                    child.style = disnake.ButtonStyle.blurple
                elif value == self.O:
                    child.emoji = "⭕"
                    child.style = disnake.ButtonStyle.green
                break

    # This method checks for the board winner
    def check_board_winner(self):
        """
        This method checks for the board winner
        :return: 1 if X wins, -1 if O wins, 2 if tied, None if no winner yet
        """
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

        # Create a new TicTacToe board
        view = TicTacToe(host, opponent)
        await inter.response.send_message(content=f"It is now {host.mention}'s turn", view=view)


def setup(client: Client):
    client.add_cog(TTT(client))
