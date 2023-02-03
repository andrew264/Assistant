import enum
from typing import Optional

import disnake
from disnake.ext import commands

from assistant import Client, colour_gen


class EvenOdd(enum.Enum):
    even = 0
    odd = 1


class HandCricket(commands.Cog):
    def __init__(self, client: Client):
        self.client = client

    @commands.slash_command(name="handcricket", description="Play a game of hand cricket")
    async def hand_cricket(self, inter: disnake.ApplicationCommandInteraction,
                           user1: disnake.Member = commands.Param(name="player-1", description="Select First Player"),
                           user2: disnake.Member = commands.Param(name="player-2",
                                                                  description="Select Second Player (defaults to you)",
                                                                  default=lambda inter: inter.author),
                           ) -> None:
        if user1 == user2:
            await inter.response.send_message("You can't play against yourself.")
            return
        logger = self.client.logger

        class SelectEvenOdd(disnake.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
                self.is_selected = False

            async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
                if self.is_selected:
                    await interaction.response.send_message("Only one can Select.", ephemeral=True)
                    return False
                if interaction.user == user1 or interaction.user == user2:
                    return True
                else:
                    await interaction.response.send_message("Start your own game with `/handcricket`", ephemeral=True)
                    return False

            def disable(self):
                for child in self.children:
                    child.disabled = True
                self.stop()

            @disnake.ui.button(label="Even", style=disnake.ButtonStyle.green)
            async def even(self, button: disnake.ui.Button, interaction: disnake.Interaction):
                self.is_selected = True
                num_view = TossNumberView()
                if interaction.user == user1:
                    num_view.choices = {user1: EvenOdd.even, user2: EvenOdd.odd}
                else:
                    num_view.choices = {user1: EvenOdd.odd, user2: EvenOdd.even}
                self.disable()
                await interaction.response.edit_message(f"{interaction.user.mention} selected Even.", view=self)
                await interaction.followup.send("Select a number", view=num_view)

            @disnake.ui.button(label="Odd", style=disnake.ButtonStyle.red)
            async def odd(self, button: disnake.ui.Button, interaction: disnake.Interaction):
                self.is_selected = True
                num_view = TossNumberView()
                if interaction.user == user1:
                    num_view.choices = {user1: EvenOdd.odd, user2: EvenOdd.even}
                else:
                    num_view.choices = {user1: EvenOdd.even, user2: EvenOdd.odd}
                self.disable()
                await interaction.response.edit_message(f"{interaction.user.mention} selected Odd.", view=self)
                await interaction.followup.send("Select a number", view=num_view)

        class TossNumberView(disnake.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
                self.choices: dict[disnake.Member, Optional[EvenOdd]] = {user1: None, user2: None}
                self.user1_choice: Optional[int] = None
                self.user2_choice: Optional[int] = None
                num = 1
                for i in range(0, 2):
                    for j in range(0, 3):
                        self.add_item(TossNumberButton(num, row=i))
                        num += 1

            async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
                if interaction.user == user1 and self.user1_choice is None:
                    return True
                elif interaction.user == user2 and self.user2_choice is None:
                    return True
                else:
                    await interaction.response.send_message("Start your own game with `/handcricket`", ephemeral=True)
                    return False

            def disable(self):
                for child in self.children:
                    child.disabled = True
                self.stop()

        class TossNumberButton(disnake.ui.Button["TossNumberButton"]):
            def __init__(self, number: int, row: int):
                super().__init__(label=str(number), style=disnake.ButtonStyle.grey,
                                 custom_id=f"number-{number}", row=row)
                self.number = number

            async def callback(self, interaction: disnake.Interaction):
                assert self.view is not None
                num_view: TossNumberView = self.view
                if interaction.user == user1:
                    num_view.user1_choice = self.number
                    await interaction.response.edit_message(f"{user1.mention} selected", view=num_view)
                elif interaction.user == user2:
                    num_view.user2_choice = self.number
                    await interaction.response.edit_message(f"{user2.mention} selected", view=num_view)
                if all([num_view.user1_choice, num_view.user2_choice]):
                    num_view.disable()
                    msg: str = (
                        f"{user1.mention} selected {num_view.user1_choice}\n"
                        f"{user2.mention} selected {num_view.user2_choice}\n"
                        f"Sum of the numbers is {num_view.user1_choice + num_view.user2_choice}\n"
                        f"which is {'Even' if (num_view.user1_choice + num_view.user2_choice) % 2 == 0 else 'Odd'}.\n"
                        f"{'-' * 40}\n"
                    )

                    if (num_view.user1_choice + num_view.user2_choice) % 2 == num_view.choices[user1].value:
                        msg += f"\n{user1.mention} won the toss."
                        await interaction.edit_original_message(msg, view=None)
                        await interaction.followup.send("Select Bat or Bowl", view=ChoseToBatOrBowl(user1))
                    else:
                        msg += f"\n{user2.mention} won the toss."
                        await interaction.edit_original_message(msg, view=None)
                        await interaction.followup.send("Select Bat or Bowl", view=ChoseToBatOrBowl(user2))

        class ChoseToBatOrBowl(disnake.ui.View):
            def __init__(self, user: disnake.Member):
                super().__init__(timeout=60)
                self.user = user

            async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
                if interaction.user == self.user:
                    self.disable()
                    return True
                else:
                    await interaction.response.send_message("Start your own game with `/handcricket`", ephemeral=True)
                    return False

            def disable(self):
                for child in self.children:
                    child.disabled = True
                self.stop()

            @disnake.ui.button(label="Bat", emoji="🏏")
            async def bat(self, button: disnake.ui.Button, interaction: disnake.Interaction):
                button.style = disnake.ButtonStyle.green
                await interaction.response.edit_message(f"{interaction.user.mention} chose to Bat.", view=self)
                game_view = Game(batting=interaction.user)
                await interaction.followup.send(f"{game_view.batting.mention} is Batting", view=game_view)

            @disnake.ui.button(label="Bowl", emoji="⚾")
            async def bowl(self, button: disnake.ui.Button, interaction: disnake.Interaction):
                button.style = disnake.ButtonStyle.green
                await interaction.response.edit_message(f"{interaction.user.mention} chose to Bowl.", view=self)
                game_view = Game(batting=user1 if interaction.user == user2 else user2)
                await interaction.followup.send(f"{game_view.batting.mention} is Batting", view=game_view)

        class Game(disnake.ui.View):
            children: list[TossNumberButton]

            def __init__(self, batting: disnake.Member):
                super().__init__()
                self.player1 = user1
                self.player2 = user2
                self.last_score: dict[disnake.Member, Optional[int]] = {user1: None, user2: None}
                self.scores: dict[disnake.Member, int] = {user1: 0, user2: 0}
                self.batting: disnake.Member = batting
                self.innings = 0

                num = 1
                for i in range(0, 2):
                    for j in range(0, 5):
                        self.add_item(GameNumberButton(num, row=i))
                        num += 1

            @property
            def embed(self):
                embed = disnake.Embed(title="Hand Cricket Scoreboard",
                                      color=colour_gen(self.batting.id))
                embed.add_field(name=f"{self.player1.display_name}", value=self.scores[self.player1], inline=True)
                embed.add_field(name=f"{self.player2.display_name}", value=self.scores[self.player2], inline=True)
                if self.last_score[self.player1] is not None and self.last_score[self.player2] is not None:
                    max_name_len = max(len(self.player1.display_name), len(self.player2.display_name))
                    embed.set_footer(
                        text=f"Last Selected:\n"
                             f"{self.player1.display_name.ljust(max_name_len)} - {self.last_score[self.player1]}\n"
                             f"{self.player2.display_name.ljust(max_name_len)} - {self.last_score[self.player2]}"
                    )
                return embed

            async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
                if interaction.user == self.player1 or interaction.user == self.player2:
                    return True
                else:
                    await interaction.response.send_message("Start your own game with `/handcricket`", ephemeral=True)
                    return False

            def disable(self):
                for child in self.children:
                    child.disabled = True
                self.stop()

            async def on_timeout(self):
                self.disable()

        class GameNumberButton(disnake.ui.Button["GameNumberButton"]):
            def __init__(self, number: int, row: int):
                super().__init__(label=str(number), style=disnake.ButtonStyle.grey,
                                 custom_id=f"number-{number}", row=row)
                self.number = number

            def is_player_turn_valid(self, player: disnake.Member, ) -> bool:
                game_view: Game = self.view
                if player == game_view.player1 and game_view.last_score[game_view.player1] is None:
                    return True
                elif player == game_view.player2 and game_view.last_score[game_view.player2] is None:
                    return True
                else:
                    return False

            def get_other_player(self, player: disnake.Member) -> disnake.Member:
                game_view: Game = self.view
                logger.debug(f"Called: get_other_player({player})")
                logger.debug(f"Players: {game_view.player1} - {game_view.player2}")
                if player.id == game_view.player1.id:
                    logger.debug(f"Returning: {game_view.player2}")
                    return game_view.player2
                else:
                    logger.debug(f"Returning: {game_view.player1}")
                    return game_view.player1

            def is_inning_over(self) -> bool:
                game_view: Game = self.view
                logger.debug(
                    f"Called: is_inning_over(): "
                    f"Last: - {game_view.last_score[game_view.player1]} - {game_view.last_score[game_view.player2]}")
                return (game_view.innings == 0 and
                        game_view.last_score[game_view.player1] == game_view.last_score[game_view.player2]
                        and self.both_selected())

            def is_game_over(self) -> bool:
                game_view: Game = self.view
                logger.debug(f"Called: is_game_over() - {game_view.innings} innings, ")
                logger.debug(f"Scores: {game_view.scores[game_view.player1]} - {game_view.scores[game_view.player2]}")
                logger.debug(
                    f"Last: {game_view.last_score[game_view.player1]} - {game_view.last_score[game_view.player2]}")
                if game_view.innings == 1:
                    logger.debug(f"Game Over: {game_view.scores[game_view.batting]} > {game_view.scores[self.get_other_player(game_view.batting)]}")
                    if game_view.scores[game_view.batting] > game_view.scores[self.get_other_player(game_view.batting)]:
                        return True
                    elif (game_view.last_score[game_view.player1] == game_view.last_score[game_view.player2]
                          and self.both_selected()):
                        return True
                return False

            def reset_last_score(self):
                game_view: Game = self.view
                if self.both_selected():
                    logger.debug(f"Resetting last score: {game_view.last_score.values()}")
                    game_view.last_score = {game_view.player1: None, game_view.player2: None}
                else:
                    logger.debug("Not resetting last score", game_view.last_score)

            def both_selected(self):
                game_view: Game = self.view
                return (game_view.last_score[game_view.player1] is not None
                        and game_view.last_score[game_view.player2] is not None)

            async def update_score(self, interaction: disnake.Interaction):
                logger.debug("Updating score")
                game_view: Game = self.view
                if self.both_selected():
                    if game_view.last_score[game_view.player1] != game_view.last_score[game_view.player2]:
                        game_view.scores[game_view.batting] += game_view.last_score[game_view.batting]
                    await interaction.edit_original_message(embed=game_view.embed, view=game_view)

            async def callback(self, interaction: disnake.Interaction):
                assert self.view is not None
                game_view: Game = self.view
                if self.is_player_turn_valid(interaction.user):
                    game_view.last_score[interaction.user] = self.number
                    await interaction.response.edit_message(embed=game_view.embed, view=game_view)
                    await self.update_score(interaction)
                else:
                    await interaction.response.send_message(
                        f"Let {self.get_other_player(interaction.user).mention} Choose.",
                        ephemeral=True)
                    return
                if self.is_inning_over():
                    logger.debug("Inning Over")
                    game_view.innings += 1
                    logger.debug(f"Switching batting player from {game_view.batting} to {self.get_other_player(game_view.batting)}")
                    game_view.batting = self.get_other_player(game_view.batting)
                    self.reset_last_score()
                    await interaction.edit_original_message(content=f"{game_view.batting.mention} is Batting",
                                                            embed=game_view.embed,
                                                            view=game_view)
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
                    await interaction.edit_original_message(content=msg, embed=game_view.embed, view=None)
                    return
                self.reset_last_score()

        view = SelectEvenOdd()
        await inter.response.send_message(f"{user1.mention}/{user2.mention}, select Even or Odd.", view=view)


def setup(client):
    client.add_cog(HandCricket(client))
