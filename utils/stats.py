import logging
from typing import Any, Dict, Optional

from motor.motor_asyncio import AsyncIOMotorClient

from config import DATABASE_NAME

logger = logging.getLogger(__name__)

DEFAULT_ELO = 1000
K_FACTOR = 32
GAME_NAMES = ["tictactoe", "rps", "handcricket"]


# --- Database Interaction ---

async def get_db_collection(database: AsyncIOMotorClient):
    """Gets the game_stats collection from the database."""
    db = database[DATABASE_NAME]
    return db["game_stats"]


async def get_player_stats(collection, user_id: int, guild_id: int, game_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Fetches stats for a player in a specific guild, optionally for a specific game."""
    composite_id = {"user_id": user_id, "guild_id": guild_id}
    projection = {"_id": 0}  # Exclude the composite _id itself from the result document
    if game_name:
        projection[f"games.{game_name}"] = 1
    else:
        projection["games"] = 1  # Fetch all games if no specific game is requested

    stats_doc = await collection.find_one({"_id": composite_id}, projection)

    if not stats_doc:
        return None

    if game_name:
        # Return the specific game stats or None if the game doesn't exist for the player
        return stats_doc.get("games", {}).get(game_name)
    else:
        # Return the entire 'games' dictionary
        return stats_doc.get("games")


async def _ensure_player_game_stats(collection, user_id: int, guild_id: int, game_name: str) -> Optional[Dict[str, Any]]:
    """Ensures the player and specific game stats structure exists for a guild, returning the game stats."""
    composite_id = {"user_id": user_id, "guild_id": guild_id}

    # Check if player-guild document exists, create if not
    await collection.update_one({"_id": composite_id}, {"$setOnInsert": {"_id": composite_id, "games": {}}}, upsert=True)

    # Check if the specific game stats exist within the player-guild document, create if not
    update_result = await collection.update_one({"_id": composite_id, f"games.{game_name}": {"$exists": False}}, {
        "$set": {
            f"games.{game_name}": {
                "wins": 0, "losses": 0, "ties": 0, "elo": DEFAULT_ELO, "matches_played": 0
            }
        }
    })
    if update_result.modified_count > 0:
        logger.debug(f"Initialized {game_name} stats for user {user_id} in guild {guild_id}")

    # Fetch the potentially updated stats
    return await get_player_stats(collection, user_id, guild_id, game_name)


# --- Elo Calculation ---

def calculate_expected_score(rating_a: float, rating_b: float) -> float:
    """Calculates the expected score for player A against player B."""
    return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))


async def update_elo(collection, winner_id: int, loser_id: int, guild_id: int, game_name: str, is_tie: bool = False):
    """Calculates and updates Elo ratings for two players after a match within a specific guild."""
    try:
        winner_stats = await _ensure_player_game_stats(collection, winner_id, guild_id, game_name)
        loser_stats = await _ensure_player_game_stats(collection, loser_id, guild_id, game_name)

        if not winner_stats or not loser_stats:
            logger.error(f"Could not retrieve/initialize stats for Elo update ({game_name}, Guild {guild_id}): {winner_id} vs {loser_id}")
            return

        winner_elo = winner_stats.get("elo", DEFAULT_ELO)
        loser_elo = loser_stats.get("elo", DEFAULT_ELO)

        expected_winner = calculate_expected_score(winner_elo, loser_elo)
        expected_loser = calculate_expected_score(loser_elo, winner_elo)

        if is_tie:
            actual_winner = 0.5
            actual_loser = 0.5
        else:
            actual_winner = 1.0
            actual_loser = 0.0

        new_winner_elo = winner_elo + K_FACTOR * (actual_winner - expected_winner)
        new_loser_elo = loser_elo + K_FACTOR * (actual_loser - expected_loser)

        # Update database using the composite _id
        winner_composite_id = {"user_id": winner_id, "guild_id": guild_id}
        loser_composite_id = {"user_id": loser_id, "guild_id": guild_id}

        await collection.update_one({"_id": winner_composite_id}, {"$set": {f"games.{game_name}.elo": new_winner_elo}})
        await collection.update_one({"_id": loser_composite_id}, {"$set": {f"games.{game_name}.elo": new_loser_elo}})
        logger.debug(f"Elo Updated ({game_name}, Guild {guild_id}): {winner_id} ({winner_elo:.1f} -> {new_winner_elo:.1f}), {loser_id} ({loser_elo:.1f} -> {new_loser_elo:.1f})")

    except Exception as e:
        logger.error(f"Error updating Elo for {game_name} (Guild {guild_id}, {winner_id} vs {loser_id}): {e}", exc_info=True)


# --- Stats Recording Utility ---

async def record_game_result(database: AsyncIOMotorClient, winner_id: int, loser_id: int, guild_id: int, game_name: str, is_tie: bool = False):
    """Records the result of a game (W/L/T) and updates Elo ratings for a specific guild."""
    if game_name not in GAME_NAMES:
        logger.warning(f"Attempted to record stats for unknown game: {game_name}")
        return
    if winner_id == loser_id and not is_tie:
        logger.warning(f"Winner and loser are the same ({winner_id}) but not a tie for {game_name} in Guild {guild_id}. Skipping.")
        return

    try:
        collection = await get_db_collection(database)
    except ConnectionError as e:
        logger.error(f"Cannot record game result: {e}")
        return

    try:
        # Ensure stats structures exist before incrementing
        await _ensure_player_game_stats(collection, winner_id, guild_id, game_name)
        await _ensure_player_game_stats(collection, loser_id, guild_id, game_name)

        # Define composite IDs
        winner_composite_id = {"user_id": winner_id, "guild_id": guild_id}
        loser_composite_id = {"user_id": loser_id, "guild_id": guild_id}

        # Update W/L/T and matches played
        if is_tie:
            await collection.update_one({"_id": winner_composite_id}, {"$inc": {f"games.{game_name}.ties": 1, f"games.{game_name}.matches_played": 1}})
            await collection.update_one({"_id": loser_composite_id}, {"$inc": {f"games.{game_name}.ties": 1, f"games.{game_name}.matches_played": 1}})
            logger.debug(f"Recorded Tie ({game_name}, Guild {guild_id}): {winner_id} vs {loser_id}")
        else:
            await collection.update_one({"_id": winner_composite_id}, {"$inc": {f"games.{game_name}.wins": 1, f"games.{game_name}.matches_played": 1}})
            await collection.update_one({"_id": loser_composite_id}, {"$inc": {f"games.{game_name}.losses": 1, f"games.{game_name}.matches_played": 1}})
            logger.debug(f"Recorded Win/Loss ({game_name}, Guild {guild_id}): Winner={winner_id}, Loser={loser_id}")

        # Update Elo
        await update_elo(collection, winner_id, loser_id, guild_id, game_name, is_tie)

    except Exception as e:
        logger.error(f"Failed to record game result for {game_name} (Guild {guild_id}, {winner_id} vs {loser_id}): {e}", exc_info=True)
