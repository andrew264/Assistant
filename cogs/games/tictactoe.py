import random
from math import inf
from typing import List, Optional, Union

import discord
from discord import app_commands
from discord.ext import commands

from assistant import AssistantBot


class TicTacToeButton(discord.ui.Button["TicTacToe"]):
    def __init__(self, x: int, y: int):
        super().__init__(style=discord.ButtonStyle.secondary, label="\u200b", row=y)
        self.x = x
        self.y = y

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        assert self.view is not None
        view: TicTacToe = self.view
        player_1 = view.player_1
        player_2 = view.player_2
        if view.board[self.y][self.x] in (view.X, view.O):  # if the cell is occupied already
            return

        if interaction.user == view.current_player:
            view.update_board(self.y, self.x)
            if view.current_player.bot:
                await view.make_a_move()
        else:
            await interaction.response.send_message(content="Wait for your turn!", ephemeral=True)
            return

        match await view.check_board_winner():
            case view.X:
                content = f"{player_1.mention} won! against {player_2.mention}"
                view.stop()
            case view.O:
                content = f"{player_2.mention} won! against {player_1.mention}"
                view.stop()
            case view.Tie:
                content = f"{player_1.mention} and {player_2.mention} tied!"
                view.stop()
            case _:
                content = f"It is now {view.current_player.mention}'s turn"

        await interaction.edit_original_response(content=content, view=view)


# This is our actual board View
class TicTacToe(discord.ui.View):
    children: List[TicTacToeButton]
    X: int = -1
    O: int = 1
    Tie: int = 2

    def __init__(self, player_1: Union[discord.Member, discord.User], player_2: Union[discord.Member, discord.User]):
        super().__init__()
        self.current_player: Union[discord.Member, discord.User] = player_1
        self.board: List[List[int]] = [[0, 0, 0],
                                       [0, 0, 0],
                                       [0, 0, 0]]
        self.player_1 = player_1
        self.player_2 = player_2

        # Our board is made up of 3 by 3 TicTacToeButtons
        for x in range(3):
            for y in range(3):
                self.add_item(TicTacToeButton(x, y))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user == self.player_1 or interaction.user == self.player_2:
            return True
        await interaction.response.send_message(content="Start your OWN Game with `/tictactoe`", ephemeral=True)
        return False

    def stop(self) -> None:
        for child in self.children:
            child.disabled = True
        super().stop()

    def switch_current_player(self):
        if self.current_player == self.player_1:
            self.current_player = self.player_2
        else:
            self.current_player = self.player_1

    def update_board(self, x: int, y: int):
        value = self.X if self.current_player == self.player_1 else self.O
        self.board[x][y] = value
        # self.print_board()
        for child in self.children:
            if child.x == y and child.y == x:
                child.disabled = True
                if value == self.X:
                    child.emoji = "❌"
                    child.style = discord.ButtonStyle.blurple
                elif value == self.O:
                    child.emoji = "⭕"
                    child.style = discord.ButtonStyle.green
                break
        self.switch_current_player()

    async def empty_cells(self):
        """
        Each empty cell will be added into cells' list
        :return: a list of empty cells
        """
        cells = []

        for x, row in enumerate(self.board):
            for y, cell in enumerate(row):
                if cell == 0:
                    cells.append([x, y])
        return cells

    async def minimax(self, depth, player):
        """
        AI function that choice the best move
        :param depth: node index in the tree (0 <= depth <= 9)
        :param player: a human or a computer
        :return: a list with [the best row, the best col, best score]
        """
        best = [-1, -1, -inf] if player == self.O else [-1, -1, +inf]

        if depth == 0 or await self.check_board_winner() is not None:
            score = await self.check_board_winner()
            return [-1, -1, score]

        for cell in await self.empty_cells():
            x, y = cell[0], cell[1]
            self.board[x][y] = player
            score = await self.minimax(depth - 1, -player)
            self.board[x][y] = 0
            score[0], score[1] = x, y

            if player == self.O:
                if score[2] > best[2]:
                    best = score  # max value
            else:
                if score[2] < best[2]:
                    best = score  # min value

        return best

    async def make_a_move(self):
        depth = len(await self.empty_cells())
        if depth == 0 or await self.check_board_winner() is not None:
            return
        if depth == 9:
            x = random.randint(0, 2)
            y = random.randint(0, 2)
        else:
            if self.current_player == self.player_1:
                move = await self.minimax(depth, self.X)
            else:
                move = await self.minimax(depth, self.O)
            x, y = move[0], move[1]
        self.update_board(x, y)

    # This method checks for the board winner
    async def check_board_winner(self):
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

    def print_board(self):
        print("-------------")
        for row in self.board:
            print("|", end=" ")
            for cell in row:
                if cell == self.X:
                    print("X", end=" | ")
                elif cell == self.O:
                    print("O", end=" | ")
                else:
                    print(" ", end=" | ")
            print("\n-------------")


class TTT(commands.Cog):
    def __init__(self, bot: AssistantBot):
        self.bot = bot

    @commands.hybrid_command(name='tictactoe', aliases=['ttt'], description='Play a game of TicTacToe with someone', )
    @app_commands.rename(player_2="opponent")
    @app_commands.describe(player_2="The player you want to play against")
    async def ttt(self, ctx: commands.Context,
                  player_2: Optional[Union[discord.Member, discord.User]] = None):
        if player_2 is None:
            assert isinstance(ctx.me, (discord.Member, discord.User))
            player_2 = ctx.me
        player_1 = ctx.author

        if player_1 == player_2:
            await ctx.send(content="You can't play against yourself! duh")
            return

        # randomly swap players
        if random.random() > 0.5:
            player_1, player_2 = player_2, player_1

        # Create a new TicTacToe board
        view = TicTacToe(player_1, player_2)
        msg = await ctx.send(content=f"It is now {view.current_player.mention}'s turn",
                             view=view)
        if view.current_player.bot:  # if player_1 is a bot, make the first move
            await view.make_a_move()
            await msg.edit(content=f"It is now {view.current_player.mention}'s turn",
                           view=view)


async def setup(bot: AssistantBot):
    await bot.add_cog(TTT(bot))
