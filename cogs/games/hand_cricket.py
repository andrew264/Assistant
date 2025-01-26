import enum
from typing import Optional, Union

import discord
from discord import app_commands
from discord.ext import commands

from assistant import AssistantBot


class EvenOdd(enum.Enum):
    even = 0
    odd = 1


class HandCricket(commands.Cog):
    def __init__(self, bot: AssistantBot):
        self.bot = bot

    @commands.hybrid_command(name="handcricket", description="Play a game of hand cricket", aliases=["hc"])
    @app_commands.describe(user1="The first player", user2="The second player")
    @app_commands.rename(user1="player-1", user2="player-2")
    @commands.guild_only()
    async def hand_cricket(self, ctx: commands.Context, user1: discord.Member, user2: Optional[discord.Member] = None) -> None:
        assert isinstance(ctx.author, discord.Member)
        if not user2:
            user2 = ctx.author
        if user1 == user2:
            await ctx.send(content="You can't play against yourself.")
            return
        if user1.bot or user2.bot:
            await ctx.send(content="You can't play against a bot.")
            return
        logger = self.bot.logger

        class SelectEvenOdd(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
                self.is_selected = False

            async def interaction_check(self, interaction: discord.Interaction) -> bool:
                assert user2
                if self.is_selected:
                    await interaction.response.send_message(content="Only one can Select.", ephemeral=True)
                    return False
                if interaction.user == user1 or interaction.user == user2:
                    return True
                else:
                    await interaction.response.send_message(content="Start your own game with `/handcricket`", ephemeral=True)
                    return False

            def disable(self):
                for child in self.children:
                    if isinstance(child, discord.ui.Button):
                        child.disabled = True
                self.stop()

            @discord.ui.button(label="Even", style=discord.ButtonStyle.green)
            async def even(self, interaction: discord.Interaction, button: discord.ui.Button):
                assert user2
                self.is_selected = True
                num_view = TossNumberView()
                if interaction.user == user1:
                    num_view.choices = {user1: EvenOdd.even, user2: EvenOdd.odd}
                else:
                    num_view.choices = {user1: EvenOdd.odd, user2: EvenOdd.even}
                self.disable()
                await interaction.response.edit_message(content=f"{interaction.user.mention} selected Even.", view=self)
                await interaction.followup.send(content="Select a number", view=num_view)

            @discord.ui.button(label="Odd", style=discord.ButtonStyle.red)
            async def odd(self, interaction: discord.Interaction, button: discord.ui.Button):
                assert user2
                self.is_selected = True
                num_view = TossNumberView()
                if interaction.user == user1:
                    num_view.choices = {user1: EvenOdd.odd, user2: EvenOdd.even}
                else:
                    num_view.choices = {user1: EvenOdd.even, user2: EvenOdd.odd}
                self.disable()
                await interaction.response.edit_message(content=f"{interaction.user.mention} selected Odd.", view=self)
                await interaction.followup.send(content="Select a number", view=num_view)

        class TossNumberView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
                assert user2
                self.choices: dict[Union[discord.Member, discord.User], EvenOdd] = {}
                self.user1_choice: Optional[int] = None
                self.user2_choice: Optional[int] = None
                num = 1
                for i in range(0, 2):
                    for j in range(0, 3):
                        self.add_item(TossNumberButton(num, row=i))  # type: ignore
                        num += 1

            async def interaction_check(self, interaction: discord.Interaction) -> bool:
                if interaction.user == user1:
                    if self.user1_choice is None:
                        return True
                    else:
                        await interaction.response.send_message(content=f"You have already selected {self.user1_choice}", ephemeral=True)
                        return False
                elif interaction.user == user2:
                    if self.user2_choice is None:
                        return True
                    else:
                        await interaction.response.send_message(content=f"You have already selected {self.user2_choice}", ephemeral=True)
                        return False
                else:
                    await interaction.response.send_message(content="Start your own game with `/handcricket`", ephemeral=True)
                    return False

            def disable(self):
                for child in self.children:
                    if isinstance(child, discord.ui.Button):
                        child.disabled = True
                self.stop()

        class TossNumberButton(discord.ui.Button["TossNumberButton"]):
            def __init__(self, number: int, row: int):
                super().__init__(label=str(number), style=discord.ButtonStyle.grey, custom_id=f"number-{number}", row=row)
                self.number = number

            async def callback(self, interaction: discord.Interaction):
                assert self.view is not None
                assert user2
                num_view: TossNumberView = self.view  # type: ignore
                if interaction.user == user1:
                    num_view.user1_choice = self.number
                    await interaction.response.edit_message(content=f"{user1.mention} selected", view=num_view)
                elif interaction.user == user2:
                    num_view.user2_choice = self.number
                    await interaction.response.edit_message(content=f"{user2.mention} selected", view=num_view)
                if all([num_view.user1_choice, num_view.user2_choice]):
                    num_view.disable()
                    assert num_view.user1_choice is not None
                    assert num_view.user2_choice is not None
                    msg: str = (f"{user1.mention} selected {num_view.user1_choice}\n"
                                f"{user2.mention} selected {num_view.user2_choice}\n"
                                f"Sum of the numbers is {num_view.user1_choice + num_view.user2_choice}\n"
                                f"which is {'Even' if (num_view.user1_choice + num_view.user2_choice) % 2 == 0 else 'Odd'}.\n"
                                f"{'-' * 40}\n")

                    if (num_view.user1_choice + num_view.user2_choice) % 2 == num_view.choices[user1].value:
                        msg += f"\n{user1.mention} won the toss."
                        await interaction.edit_original_response(content=msg, view=None)
                        await interaction.followup.send(content="Select Bat or Bowl", view=ChoseToBatOrBowl(user1))
                    else:
                        msg += f"\n{user2.mention} won the toss."
                        await interaction.edit_original_response(content=msg, view=None)
                        await interaction.followup.send(content=f"Select Bat or Bowl", view=ChoseToBatOrBowl(user2))

        class ChoseToBatOrBowl(discord.ui.View):
            def __init__(self, user: discord.Member):
                super().__init__(timeout=60)
                self.user = user

            async def interaction_check(self, interaction: discord.Interaction) -> bool:
                if interaction.user == self.user:
                    self.disable()
                    return True
                else:
                    await interaction.response.send_message(content="Start your own game with `/handcricket`", ephemeral=True)
                    return False

            def disable(self):
                for child in self.children:
                    if isinstance(child, discord.ui.Button):
                        child.disabled = True
                self.stop()

            @discord.ui.button(label="Bat", emoji="🏏")
            async def bat(self, interaction: discord.Interaction, button: discord.ui.Button):
                assert isinstance(interaction.user, discord.Member)
                button.style = discord.ButtonStyle.green
                await interaction.response.edit_message(content=f"{interaction.user.mention} chose to Bat.", view=self)
                game_view = Game(batting=interaction.user)
                await interaction.followup.send(content=f"{game_view.batting.mention} is Batting", view=game_view)

            @discord.ui.button(label="Bowl", emoji="⚾")
            async def bowl(self, interaction: discord.Interaction, button: discord.ui.Button):
                assert user2
                button.style = discord.ButtonStyle.green
                await interaction.response.edit_message(content=f"{interaction.user.mention} chose to Bowl.", view=self)
                game_view = Game(batting=user1 if interaction.user == user2 else user2)
                await interaction.followup.send(content=f"{game_view.batting.mention} is Batting", view=game_view)

        class Game(discord.ui.View):
            children: list[TossNumberButton]

            def __init__(self, batting: discord.Member):
                super().__init__()
                assert user2
                self.player1 = user1
                self.player2 = user2
                self.last_score: dict[Union[discord.Member, discord.User], Optional[int]] = {user1: None, user2: None}
                self.scores: dict[discord.Member, int] = {user1: 0, user2: 0}
                self.batting = batting
                self.innings = 0

                num = 1
                for i in range(0, 2):
                    for j in range(0, 5):
                        self.add_item(GameNumberButton(num, row=i))
                        num += 1

            @property
            def embed(self):
                embed = discord.Embed(title="Hand Cricket Scoreboard", color=discord.Color.blurple())
                embed.add_field(name=f"{self.player1.display_name}", value=self.scores[self.player1], inline=True)
                embed.add_field(name=f"{self.player2.display_name}", value=self.scores[self.player2], inline=True)
                if self.last_score[self.player1] is not None and self.last_score[self.player2] is not None:
                    max_name_len = max(len(self.player1.display_name), len(self.player2.display_name))
                    embed.set_footer(text=f"Last Selected:\n"
                                          f"{self.player1.display_name.ljust(max_name_len)} - {self.last_score[self.player1]}\n"
                                          f"{self.player2.display_name.ljust(max_name_len)} - {self.last_score[self.player2]}")
                return embed

            async def interaction_check(self, interaction: discord.Interaction) -> bool:
                if interaction.user == self.player1 or interaction.user == self.player2:
                    return True
                else:
                    await interaction.response.send_message(content="Start your own game with `/handcricket`", ephemeral=True)
                    return False

            def disable(self):
                for child in self.children:
                    child.disabled = True
                self.stop()

            async def on_timeout(self):
                self.disable()

        class GameNumberButton(discord.ui.Button):
            def __init__(self, number: int, row: int):
                super().__init__(label=str(number), style=discord.ButtonStyle.grey, custom_id=f"number-{number}", row=row)
                self.number = number

            def is_player_turn_valid(self, player: Union[discord.Member, discord.User], ) -> bool:
                game_view: Game = self.view  # type: ignore
                if player == game_view.player1 and game_view.last_score[game_view.player1] is None:
                    return True
                elif player == game_view.player2 and game_view.last_score[game_view.player2] is None:
                    return True
                else:
                    return False

            def get_other_player(self, player: Union[discord.Member, discord.User]) -> discord.Member:
                game_view: Game = self.view  # type: ignore
                logger.debug(f"Called: get_other_player({player})")
                logger.debug(f"Players: {game_view.player1} - {game_view.player2}")
                if player.id == game_view.player1.id:
                    logger.debug(f"Returning: {game_view.player2}")
                    return game_view.player2
                else:
                    logger.debug(f"Returning: {game_view.player1}")
                    return game_view.player1

            def is_inning_over(self) -> bool:
                game_view: Game = self.view  # type: ignore
                logger.debug(f"Called: is_inning_over(): "
                             f"Last: - {game_view.last_score[game_view.player1]} - {game_view.last_score[game_view.player2]}")
                return (game_view.innings == 0 and game_view.last_score[game_view.player1] == game_view.last_score[game_view.player2] and self.both_selected())

            def is_game_over(self) -> bool:
                game_view: Game = self.view  # type: ignore
                logger.debug(f"Called: is_game_over() - {game_view.innings} innings, ")
                logger.debug(f"Scores: {game_view.scores[game_view.player1]} - {game_view.scores[game_view.player2]}")
                logger.debug(f"Last: {game_view.last_score[game_view.player1]} - {game_view.last_score[game_view.player2]}")
                if game_view.innings == 1:
                    logger.debug(f"Game Over: "
                                 f"{game_view.scores[game_view.batting]} > "
                                 f"{game_view.scores[self.get_other_player(game_view.batting)]}")
                    if game_view.scores[game_view.batting] > game_view.scores[self.get_other_player(game_view.batting)]:
                        return True
                    elif (game_view.last_score[game_view.player1] == game_view.last_score[game_view.player2] and self.both_selected()):
                        return True
                return False

            def reset_last_score(self):
                game_view: Game = self.view  # type: ignore
                if self.both_selected():
                    logger.debug(f"Resetting last score: {game_view.last_score.values()}")
                    game_view.last_score = {game_view.player1: None, game_view.player2: None}
                else:
                    logger.debug("Not resetting last score", game_view.last_score)

            def both_selected(self):
                game_view: Game = self.view  # type: ignore
                return (game_view.last_score[game_view.player1] is not None and game_view.last_score[game_view.player2] is not None)

            async def update_score(self, interaction: discord.Interaction):
                logger.debug("Updating score")
                game_view: Game = self.view  # type: ignore
                if self.both_selected():
                    if game_view.last_score[game_view.player1] != game_view.last_score[game_view.player2]:
                        last_score = game_view.last_score[game_view.batting]
                        assert last_score is not None
                        game_view.scores[game_view.batting] += last_score
                    await interaction.edit_original_response(embed=game_view.embed, view=game_view)

            async def callback(self, interaction: discord.Interaction):
                assert self.view is not None
                game_view: Game = self.view
                if self.is_player_turn_valid(interaction.user):
                    game_view.last_score[interaction.user] = self.number
                    await interaction.response.edit_message(embed=game_view.embed, view=game_view)
                    await self.update_score(interaction)
                else:
                    await interaction.response.send_message(content=f"Let {self.get_other_player(interaction.user).mention} Choose.", ephemeral=True)
                    return
                if self.is_inning_over():
                    logger.debug("Inning Over")
                    game_view.innings += 1
                    logger.debug(f"Switching batting player from {game_view.batting}"
                                 f" to {self.get_other_player(game_view.batting)}")
                    game_view.batting = self.get_other_player(game_view.batting)
                    self.reset_last_score()
                    await interaction.edit_original_response(content=f"{game_view.batting.mention} is Batting", embed=game_view.embed, view=game_view)
                    return
                if self.is_game_over():
                    logger.debug("Game Over")
                    game_view.disable()
                    if game_view.scores[game_view.player1] > game_view.scores[game_view.player2]:
                        msg = f"{game_view.player1.mention} won! against {game_view.player2.mention}"
                    elif game_view.scores[game_view.player2] > game_view.scores[game_view.player1]:
                        msg = f"{game_view.player2.mention} won! against {game_view.player1.mention}"
                    else:
                        msg = f"{game_view.player1.mention} and {game_view.player2.mention} tied!"
                    await interaction.edit_original_response(content=msg, embed=game_view.embed, view=None)
                    return
                self.reset_last_score()

        view = SelectEvenOdd()
        await ctx.send(content=f"{user1.mention}/{user2.mention}, select Even or Odd.", view=view)


async def setup(bot: AssistantBot):
    await bot.add_cog(HandCricket(bot))
