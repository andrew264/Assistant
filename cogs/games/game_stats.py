from typing import List, Optional

import discord
from discord import app_commands
from discord.ext import commands

from assistant import AssistantBot
from config import MONGO_URI
from utils.stats import DEFAULT_ELO, GAME_NAMES, get_db_collection, get_player_stats

RESULTS_PER_PAGE = 10


class GameStatsCog(commands.Cog):
    def __init__(self, bot: AssistantBot):
        self.bot = bot

    async def get_leaderboard_data(self, guild_id: int, game_name: str, limit: int = 100) -> List[dict]:
        """Fetches and sorts leaderboard data from the database for a specific guild."""
        collection = await get_db_collection(self.bot.database)
        # Query documents for the specific guild and game, sort by Elo
        cursor = collection.find({"_id.guild_id": guild_id, f"games.{game_name}": {"$exists": True}},  # Project only necessary fields, including user_id from the composite _id
                                 {"_id.user_id": 1, f"games.{game_name}": 1}).sort(f"games.{game_name}.elo", -1).limit(limit)
        return await cursor.to_list(length=limit)

    @app_commands.command(name="leaderboard", description="Shows the leaderboard for a game in this server.")
    @app_commands.describe(game="The game to show the leaderboard for.")
    @app_commands.choices(game=[app_commands.Choice(name=name.capitalize(), value=name) for name in GAME_NAMES])
    @app_commands.guild_only()
    async def leaderboard(self, interaction: discord.Interaction, game: app_commands.Choice[str]):
        await interaction.response.defer()
        assert interaction.guild_id is not None
        guild_id = interaction.guild_id
        game_name = game.value

        try:
            leaderboard_data = await self.get_leaderboard_data(guild_id, game_name, limit=RESULTS_PER_PAGE)
        except ConnectionError as e:
            await interaction.edit_original_response(content=f"Database error: {e}")
            return
        except Exception as e:
            self.bot.logger.error(f"Error fetching leaderboard for {game_name} in Guild {guild_id}: {e}", exc_info=True)
            await interaction.edit_original_response(content="An error occurred while fetching the leaderboard.")
            return

        if not leaderboard_data:
            await interaction.edit_original_response(content=f"No stats found for {game.name} in this server yet.")
            return

        embed = discord.Embed(title=f"{game.name} Leaderboard - {interaction.guild.name}", color=discord.Color.gold())

        description = ""
        for i, entry in enumerate(leaderboard_data):
            user_id = entry["_id"]["user_id"]
            stats = entry.get("games", {}).get(game_name, {})
            elo = stats.get("elo", DEFAULT_ELO)
            wins = stats.get("wins", 0)
            losses = stats.get("losses", 0)
            ties = stats.get("ties", 0)

            # Fetch user object using the extracted user_id
            user = self.bot.get_user(user_id) or f"User ID: {user_id}"
            description += f"**{i + 1}.** {user} - **Elo:** {elo:.1f} (W:{wins} L:{losses} T:{ties})\n"

        embed.description = description
        await interaction.edit_original_response(embed=embed)

    @app_commands.command(name="stats", description="Shows game statistics for a user in this server.")
    @app_commands.describe(user="The user to show stats for (defaults to you).", game="The specific game to show stats for (defaults to all games).")
    @app_commands.choices(game=[app_commands.Choice(name=name.capitalize(), value=name) for name in GAME_NAMES])
    @app_commands.guild_only()
    async def stats(self, interaction: discord.Interaction, user: Optional[discord.User] = None, game: Optional[app_commands.Choice[str]] = None):
        await interaction.response.defer()
        assert interaction.guild_id is not None
        guild_id = interaction.guild_id
        target_user = user or interaction.user
        game_name = game.value if game else None

        try:
            collection = await get_db_collection(self.bot.database)
            user_stats_data = await get_player_stats(collection, target_user.id, guild_id, game_name)
        except ConnectionError as e:
            await interaction.edit_original_response(content=f"Database error: {e}")
            return
        except Exception as e:
            self.bot.logger.error(f"Error fetching stats for {target_user.id} in Guild {guild_id} ({game_name}): {e}", exc_info=True)
            await interaction.edit_original_response(content="An error occurred while fetching stats.")
            return

        if not user_stats_data:
            await interaction.edit_original_response(content=f"{target_user.mention} hasn't played any recorded games in this server yet.")
            return

        embed = discord.Embed(title=f"Game Stats for {target_user.display_name} in {interaction.guild.name}", color=target_user.color)
        embed.set_thumbnail(url=target_user.display_avatar.url)

        if game_name:  # Specific game requested
            if not isinstance(user_stats_data, dict):
                await interaction.edit_original_response(content=f"{target_user.mention} hasn't played {game.name} in this server yet.")
                return

            elo = user_stats_data.get("elo", DEFAULT_ELO)
            wins = user_stats_data.get("wins", 0)
            losses = user_stats_data.get("losses", 0)
            ties = user_stats_data.get("ties", 0)
            matches = user_stats_data.get("matches_played", 0)
            win_rate = (wins / matches * 100) if matches > 0 else 0

            embed.add_field(name=game.name, value=(f"**Elo:** {elo:.1f}\n"
                                                   f"**Wins:** {wins}\n"
                                                   f"**Losses:** {losses}\n"
                                                   f"**Ties:** {ties}\n"
                                                   f"**Matches:** {matches}\n"
                                                   f"**Win Rate:** {win_rate:.1f}%"), inline=False)
        else:  # Show all games
            if not isinstance(user_stats_data, dict):
                await interaction.edit_original_response(content=f"{target_user.mention} hasn't played any recorded games in this server yet.")
                return

            if not user_stats_data:  # Check if the games dict is empty
                await interaction.edit_original_response(content=f"{target_user.mention} hasn't played any recorded games in this server yet.")
                return

            for g_name, g_stats in user_stats_data.items():
                if g_name not in GAME_NAMES: continue

                elo = g_stats.get("elo", DEFAULT_ELO)
                wins = g_stats.get("wins", 0)
                losses = g_stats.get("losses", 0)
                ties = g_stats.get("ties", 0)
                matches = g_stats.get("matches_played", 0)
                win_rate = (wins / matches * 100) if matches > 0 else 0

                embed.add_field(name=g_name.capitalize(), value=(f"**Elo:** {elo:.1f}\n"
                                                                 f"W/L/T: {wins}/{losses}/{ties}\n"
                                                                 f"Matches: {matches} ({win_rate:.1f}%)"), inline=True)
            # If after looping, no fields were added (e.g., user doc exists but no games played)
            if not embed.fields:
                await interaction.edit_original_response(content=f"{target_user.mention} hasn't played any recorded games in this server yet.")
                return

        await interaction.edit_original_response(embed=embed)


async def setup(bot: AssistantBot):
    if MONGO_URI:
        await bot.add_cog(GameStatsCog(bot))
        bot.logger.info("[LOADED] - info.game_stats")
    else:
        bot.logger.warning("[SKIPPED] games.game_stats - Database connection not available.")
