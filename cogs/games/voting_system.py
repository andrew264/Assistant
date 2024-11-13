import itertools
import random
from typing import Dict, List, Optional, Tuple

import discord
from discord import app_commands
from discord.ext import commands

from assistant import AssistantBot

class EloRatingSystem:
    def __init__(self, candidates: List[str], creator: int, title: str, initial_rating=1000, k_factor=32):
        self.ratings: Dict[str, float] = {}
        self.initial_rating = initial_rating
        self.k_factor = k_factor
        for c in candidates:
            self.add_candidate(c)
        self.voters: List[int] = []
        self.creator = creator
        self.title = title

    def add_candidate(self, candidate: str) -> None:
        """Add a candidate with an initial rating if not already added."""
        if candidate not in self.ratings:
            self.ratings[candidate] = self.initial_rating

    def get_all_candidates(self) -> List[str]:
        return list(self.ratings.keys())

    def add_voter(self, voter: discord.User):
        self.voters.append(voter.id)

    def has_voted_before(self, voter: discord.User):
        return voter.id in self.voters

    def get_candidate_pairings(self) -> List[Tuple[str, str]]:
        all_pairs = list(itertools.combinations(self.get_all_candidates(), 2))
        random.shuffle(all_pairs)
        return all_pairs

    def expected_score(self, rating_a: float, rating_b: float) -> float:
        """Calculate the expected score for candidate A against candidate B."""
        return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

    def update_ratings(self, winner: str, loser: str) -> None:
        """Update the Elo ratings for a winner-loser pair."""
        self.add_candidate(winner)
        self.add_candidate(loser)

        winner_rating = self.ratings[winner]
        loser_rating = self.ratings[loser]

        expected_winner = self.expected_score(winner_rating, loser_rating)
        expected_loser = self.expected_score(loser_rating, winner_rating)

        self.ratings[winner] += self.k_factor * (1 - expected_winner)
        self.ratings[loser] += self.k_factor * (0 - expected_loser)

    def get_ratings(self) -> dict:
        """Return the current Elo ratings of all candidates."""
        return dict(self.ratings)

    def summary(self):
        ratings = self.ratings
        sorted_ratings = sorted(ratings.items(), key=lambda x: x[1], reverse=True)

        highest_rating = max(ratings.values())
        lowest_rating = min(ratings.values())

        highest_rated_candidates = [name for name, rating in ratings.items() if rating == highest_rating]
        lowest_rated_candidates = [name for name, rating in ratings.items() if rating == lowest_rating]

        summary_md = f"# {self.title}\n\n"

        summary_md += "## Insights\n"
        summary_md += f"- **Highest Rating**: {highest_rating:.2f} ({', '.join(highest_rated_candidates)})\n"
        summary_md += f"- **Lowest Rating**: {lowest_rating:.2f} ({', '.join(lowest_rated_candidates)})\n"
        summary_md += f"- **Number of Voters**: {len(self.voters)}\n"

        summary_md += "## Elo Ratings\n"
        for candidate, rating in sorted_ratings:
            summary_md += f"- **{candidate}**: {rating:.2f}\n"

        return summary_md

class VoteButton(discord.ui.Button["VoteButton"], ):
    def __init__(self, winner: str, looser: str) -> None:
        self.winner: str = winner
        self.losser: str = looser
        super().__init__(label=winner, style=discord.ButtonStyle.blurple, )

    async def callback(self, interaction: discord.Interaction) -> None:
        assert self.view is not None and isinstance(self.view, VoteButtonView), "somthing is wrong, i can feel it"
        view: VoteButtonView = self.view
        view.rating_system.update_ratings(self.winner, self.losser)
        view.add_next_vote_buttons()
        if view.is_voting_complete:
            await interaction.response.edit_message(content="Voting Complete", view=None)
            view.stop()
        else:
            await interaction.response.edit_message(view=view)

class VoteButtonView(discord.ui.View):
    def __init__(self, rating_system: EloRatingSystem, ):
        super().__init__()
        self.rating_system = rating_system
        self.next_page = 0
        self.candidate_pairs = rating_system.get_candidate_pairings()
        self.add_next_vote_buttons()

    def add_next_vote_buttons(self):
        self.clear_items()
        if self.next_page < len(self.candidate_pairs):
            c1, c2 = self.candidate_pairs[self.next_page]
            self.add_item(VoteButton(c1, c2))
            self.add_item(VoteButton(c2, c1))
            self.next_page += 1

    @property
    def is_voting_complete(self) -> bool:
        return self.next_page == len(self.candidate_pairs)

class VotingSystem(commands.Cog):
    def __init__(self, bot: AssistantBot):
        self.bot = bot
        self.global_rating_system: Dict[int, EloRatingSystem] = {}

    @app_commands.command(name='vote', description='Cast your vote to find out!')
    async def vote(self, ctx: discord.Interaction):
        if ctx.channel.id not in self.global_rating_system:
            return await ctx.response.send_message('No Currently Active Polls in this channel', ephemeral=True)
        elo_rating = self.global_rating_system.get(ctx.channel.id)
        if elo_rating.has_voted_before(ctx.user):
            return await ctx.response.send_message('You have already cast your votes!', ephemeral=True)
        elo_rating.add_voter(ctx.user)
        await ctx.response.send_message(f'Select your preferred Candidate {ctx.user.mention}!', view=VoteButtonView(elo_rating), ephemeral=True)

    @app_commands.command(name='create-poll', description='Setup the candidates to vote for!')
    @app_commands.checks.has_permissions(create_polls=True)
    @app_commands.describe(title="Title for the Voting Poll", candidates="Candidates separated by commas")
    async def create_poll(self, ctx: discord.Interaction, candidates: str, title: Optional[str] = None):
        if ctx.channel.id in self.global_rating_system:
            elo_rating = self.global_rating_system.get(ctx.channel.id)
            return await ctx.response.send_message(f'There is a Active Poll in this channel by <@{elo_rating.creator}>', ephemeral=True)
        candidates = [c.strip() for c in candidates.split(',')]
        if title is None:
            title = "Voting"
        self.global_rating_system[ctx.channel.id] = EloRatingSystem(candidates=candidates, creator=ctx.user.id, title=title)
        content = f"# {title}\n"
        for c in candidates:
            content += f"- **{c}**\n"
        content += "Use `/vote` to cast your Vote."
        await ctx.response.send_message(content)

    @app_commands.command(name='poll-results', description='STOP THE COUNT and Publish the results')
    async def poll_results(self, ctx: discord.Interaction):
        if ctx.channel.id not in self.global_rating_system:
            return await ctx.response.send_message('No Currently Active Polls in this channel', ephemeral=True)
        elo_rating = self.global_rating_system.get(ctx.channel.id)
        if (elo_rating.creator != ctx.user.id) or (not ctx.user.guild_permissions.administrator):
            return await ctx.response.send_message(f'Only <@{elo_rating.creator}> can STOP THE COUNT!', ephemeral=True)
        await ctx.response.send_message(elo_rating.summary())
        self.global_rating_system.pop(ctx.channel.id)

async def setup(bot: AssistantBot):
    await bot.add_cog(VotingSystem(bot))
