import asyncio
from typing import Optional

import discord
from discord.ext import commands

from assistant import AssistantBot
from cogs.starboard.starboard_config import StarboardConfigCog
from config import DATABASE_NAME, MONGO_URI
from models.starboard_models import StarboardConfig, StarredMessage

STAR_CONTENT_FORMAT = "{emoji} **{count}** | {channel_mention}"


class StarboardCoreCog(commands.Cog, name="Starboard Core"):
    """Handles the core logic of the starboard system."""

    def __init__(self, bot: AssistantBot):
        self.bot = bot
        self._db = self.bot.database
        self._config_cog: Optional[StarboardConfigCog] = None
        self.logger = bot.logger.getChild("starboard")
        if not self._db:
            self.logger.warning("[Starboard Core] MongoDB not available. Starboard will not function.")

    @property
    def config_cog(self) -> StarboardConfigCog:
        if self._config_cog is None:
            self._config_cog = self.bot.get_cog("Starboard Config")
            if self._config_cog is None:
                raise RuntimeError("Starboard Config Cog not found!")
        return self._config_cog

    async def _ensure_indexes(self):
        """Ensures the necessary MongoDB indexes are created for the starboard feature."""
        if self.starred_messages_collection is None:
            self.logger.warning("[Starboard Core] Cannot ensure indexes: Database collection not available.")
            return

        try:
            # Define indexes
            compound_index_keys = [("guild_id", 1), ("original_message_id", 1)]
            starboard_msg_index_keys = [("guild_id", 1), ("starboard_message_id", 1)]

            # Get existing indexes
            existing_indexes = await self.starred_messages_collection.index_information()

            # Check and create compound unique index
            compound_index_name = "_".join([f"{k}_{v}" for k, v in compound_index_keys])
            if compound_index_name not in existing_indexes:
                await self.starred_messages_collection.create_index(compound_index_keys, name=compound_index_name, unique=True)
                self.logger.info(f"[Starboard Core] Created unique compound index: {compound_index_name}")
            else:
                self.logger.debug(f"[Starboard Core] Unique compound index '{compound_index_name}' already exists.")

            # Check and create optional starboard message index
            starboard_msg_index_name = "_".join([f"{k}_{v}" for k, v in starboard_msg_index_keys])
            if starboard_msg_index_name not in existing_indexes:
                await self.starred_messages_collection.create_index(starboard_msg_index_keys, name=starboard_msg_index_name, sparse=True)
                self.logger.info(f"[Starboard Core] Created optional index: {starboard_msg_index_name}")
            else:
                self.logger.debug(f"[Starboard Core] Optional index '{starboard_msg_index_name}' already exists.")

        except Exception as e:
            self.logger.error(f"[Starboard Core] Failed to ensure MongoDB indexes: {e}", exc_info=True)

    @property
    def starred_messages_collection(self):
        if not self._db: return None
        return self._db[DATABASE_NAME]["starred_messages"]

    async def _get_starred_message_entry(self, guild_id: int, original_message_id: int) -> Optional[StarredMessage]:
        """Fetches a StarredMessage entry from the database"""
        if self.starred_messages_collection is None: return None

        data = await self.starred_messages_collection.find_one({
            "guild_id": guild_id, "original_message_id": original_message_id
        })
        return StarredMessage(**data) if data else None

    async def _save_starred_message_entry(self, entry: StarredMessage):
        """Saves or updates a StarredMessage entry"""
        if self.starred_messages_collection is None: return

        filter_query = {
            "guild_id": entry.guild_id, "original_message_id": entry.original_message_id
        }
        # Prepare update data, excluding the key fields themselves if desired, though $set handles it.
        update_data = entry.model_dump(exclude={'guild_id', 'original_message_id'}, by_alias=False)

        await self.starred_messages_collection.update_one(filter_query, {"$set": update_data}, upsert=True)

    async def _delete_starred_message_entry(self, guild_id: int, original_message_id: int):
        """Deletes a StarredMessage entry"""
        if self.starred_messages_collection is None: return
        await self.starred_messages_collection.delete_one({
            "guild_id": guild_id, "original_message_id": original_message_id
        })

    # --- Helper functions ---
    async def _fetch_message_safely(self, channel_id: int, message_id: int) -> Optional[discord.Message]:
        channel = self.bot.get_channel(channel_id)
        if not isinstance(channel, (discord.TextChannel, discord.Thread, discord.VoiceChannel)):
            self.logger.warning(f"Could not find channel {channel_id} or it's not a text-based channel.")
            return None
        try:
            message = await channel.fetch_message(message_id)
            return message
        except discord.NotFound:
            self.logger.debug(f"Original message {message_id} in channel {channel_id} not found (likely deleted).")
            return None
        except discord.Forbidden:
            self.logger.warning(f"Missing permissions to fetch message {message_id} in channel {channel_id}.")
            return None
        except discord.HTTPException as e:
            self.logger.error(f"Failed to fetch message {message_id} in {channel_id}: {e}")
            return None

    @staticmethod
    def _create_starboard_embed(original_message: discord.Message, star_count: int) -> discord.Embed:
        embed = discord.Embed(description=original_message.content, color=discord.Color.gold(), timestamp=original_message.created_at)
        embed.set_author(name=original_message.author.display_name, icon_url=original_message.author.display_avatar.url, url=original_message.jump_url)
        embed.add_field(name="Original Message", value=f"[Jump!]({original_message.jump_url})", inline=False)

        image_set = False
        attachment_list = []
        for attachment in original_message.attachments:
            if not image_set and attachment.content_type and attachment.content_type.startswith("image/"):
                embed.set_image(url=attachment.url)
                image_set = True
            else:
                attachment_list.append(f"[{attachment.filename}]({attachment.url})")

        if attachment_list:
            embed.add_field(name="Attachments", value="\n".join(attachment_list), inline=False)
        return embed

    async def _create_starboard_post(self, original_message: discord.Message, entry: StarredMessage, config: StarboardConfig):
        if not config.starboard_channel_id: return
        starboard_channel = self.bot.get_channel(config.starboard_channel_id)
        if not isinstance(starboard_channel, discord.TextChannel):
            self.logger.warning(f"Starboard channel {config.starboard_channel_id} not found or not a text channel for guild {config.guild_id}.")
            return

        content = STAR_CONTENT_FORMAT.format(emoji=config.star_emoji, count=entry.star_count, channel_mention=original_message.channel.mention)
        embed = self._create_starboard_embed(original_message, entry.star_count)

        try:
            perms = starboard_channel.permissions_for(original_message.guild.me)
            if not (perms.send_messages and perms.embed_links):
                self.logger.warning(f"Missing Send/Embed permissions in starboard channel {starboard_channel.id} for guild {config.guild_id}.")
                return

            starboard_msg = await starboard_channel.send(content=content, embed=embed)
            entry.starboard_message_id = starboard_msg.id
            entry.is_posted = True
            await self._save_starred_message_entry(entry)  # Save the updated entry with the starboard_message_id
            self.logger.info(f"Posted message {original_message.id} to starboard in guild {config.guild_id}")
        except discord.Forbidden:
            self.logger.error(f"Forbidden to send message in starboard channel {starboard_channel.id} for guild {config.guild_id}.")
        except discord.HTTPException as e:
            self.logger.error(f"Failed to send starboard message for {original_message.id} in guild {config.guild_id}: {e}")

    async def _update_starboard_post(self, entry: StarredMessage, config: StarboardConfig):
        if not entry.starboard_message_id or not config.starboard_channel_id: return
        starboard_channel = self.bot.get_channel(config.starboard_channel_id)
        if not isinstance(starboard_channel, discord.TextChannel):
            self.logger.warning(f"Starboard channel {config.starboard_channel_id} invalid for update in guild {config.guild_id}.")
            return

        try:
            starboard_msg = await starboard_channel.fetch_message(entry.starboard_message_id)
            new_content = STAR_CONTENT_FORMAT.format(emoji=config.star_emoji, count=entry.star_count, channel_mention=f"<#{entry.original_channel_id}>")
            if starboard_msg.content != new_content:
                await starboard_msg.edit(content=new_content)
                self.logger.debug(f"Updated star count for starboard message {entry.starboard_message_id} in guild {config.guild_id} to {entry.star_count}")
        except discord.NotFound:
            self.logger.warning(f"Starboard message {entry.starboard_message_id} not found in guild {config.guild_id}. Unmarking as posted.")
            entry.is_posted = False
            entry.starboard_message_id = None
            await self._save_starred_message_entry(entry)  # Save the state change
        except discord.Forbidden:
            self.logger.error(f"Forbidden to edit starboard message {entry.starboard_message_id} in guild {config.guild_id}.")
        except discord.HTTPException as e:
            self.logger.error(f"Failed to edit starboard message {entry.starboard_message_id} in guild {config.guild_id}: {e}")

    async def _delete_starboard_post(self, entry: StarredMessage, config: StarboardConfig):
        if not entry.starboard_message_id or not config.starboard_channel_id: return
        starboard_channel = self.bot.get_channel(config.starboard_channel_id)
        if not isinstance(starboard_channel, discord.TextChannel):
            self.logger.warning(f"Starboard channel {config.starboard_channel_id} invalid for delete in guild {config.guild_id}.")
            return

        try:
            starboard_msg = await starboard_channel.fetch_message(entry.starboard_message_id)
            await starboard_msg.delete()
            self.logger.info(f"Deleted starboard message {entry.starboard_message_id} for original {entry.original_message_id} in guild {config.guild_id}")
        except discord.NotFound:
            self.logger.warning(f"Starboard message {entry.starboard_message_id} already deleted in guild {config.guild_id}.")
            pass  # Already deleted
        except discord.Forbidden:
            self.logger.error(f"Forbidden to delete starboard message {entry.starboard_message_id} in guild {config.guild_id}.")
        except discord.HTTPException as e:
            self.logger.error(f"Failed to delete starboard message {entry.starboard_message_id} in guild {config.guild_id}: {e}")
        finally:
            entry.is_posted = False
            entry.starboard_message_id = None
            # Save the state change even if deletion failed
            await self._save_starred_message_entry(entry)

    # --- Event Listeners ---

    @commands.Cog.listener("on_raw_reaction_add")
    async def handle_reaction_add(self, payload: discord.RawReactionActionEvent):
        # initial checks
        if not payload.guild_id or not payload.member or payload.member.bot: return
        config = await self.config_cog.get_guild_config(payload.guild_id)
        if not config.is_enabled or not config.starboard_channel_id: return
        emoji_str = str(payload.emoji)
        # Add custom emoji validation if needed
        if emoji_str != config.star_emoji: return
        if payload.channel_id == config.starboard_channel_id: return

        original_message = await self._fetch_message_safely(payload.channel_id, payload.message_id)
        if not original_message:
            await self._delete_starred_message_entry(payload.guild_id, payload.message_id)
            return

        if not config.allow_bot_messages and original_message.author.bot: return
        if not config.allow_self_star and payload.user_id == original_message.author.id: return
        if config.ignore_nsfw_channels and isinstance(original_message.channel, discord.TextChannel) and original_message.channel.is_nsfw(): return

        # --- Process Star ---
        entry = await self._get_starred_message_entry(payload.guild_id, payload.message_id)
        if not entry:
            entry = StarredMessage(guild_id=payload.guild_id, original_channel_id=payload.channel_id, original_message_id=payload.message_id)

        if entry.update_stars(payload.user_id, add=True):
            await self._save_starred_message_entry(entry)

            if entry.is_posted:
                await self._update_starboard_post(entry, config)
            elif entry.star_count >= config.threshold:
                await self._create_starboard_post(original_message, entry, config)

    @commands.Cog.listener("on_raw_reaction_remove")
    async def handle_reaction_remove(self, payload: discord.RawReactionActionEvent):
        # initial checks
        if not payload.guild_id: return
        config = await self.config_cog.get_guild_config(payload.guild_id)
        if not config.starboard_channel_id: return
        emoji_str = str(payload.emoji)
        if emoji_str != config.star_emoji: return
        if payload.channel_id == config.starboard_channel_id: return

        entry = await self._get_starred_message_entry(payload.guild_id, payload.message_id)
        if not entry: return

        if entry.update_stars(payload.user_id, add=False):
            if entry.is_posted:
                if entry.star_count < config.threshold and config.delete_if_unstarred:
                    await self._delete_starboard_post(entry, config)
                else:
                    await self._update_starboard_post(entry, config)
                    await self._save_starred_message_entry(entry)  # Save count update
            else:
                await self._save_starred_message_entry(entry)  # Save count update

    @commands.Cog.listener("on_raw_reaction_clear")
    async def handle_reaction_clear(self, payload: discord.RawReactionActionEvent):
        # initial checks
        if not payload.guild_id: return
        config = await self.config_cog.get_guild_config(payload.guild_id)
        if not config.starboard_channel_id: return

        entry = await self._get_starred_message_entry(payload.guild_id, payload.message_id)
        if not entry: return

        if entry.clear_stars():
            if entry.is_posted:
                if config.delete_if_unstarred:
                    await self._delete_starboard_post(entry, config)
                else:
                    await self._update_starboard_post(entry, config)
                    await self._save_starred_message_entry(entry)
            else:
                await self._save_starred_message_entry(entry)

    @commands.Cog.listener("on_raw_reaction_clear_emoji")
    async def handle_reaction_clear_emoji(self, payload: discord.RawReactionClearEmojiEvent):
        # initial checks
        if not payload.guild_id: return
        config = await self.config_cog.get_guild_config(payload.guild_id)
        if not config.starboard_channel_id: return
        emoji_str = str(payload.emoji)
        if emoji_str != config.star_emoji: return

        entry = await self._get_starred_message_entry(payload.guild_id, payload.message_id)
        if not entry: return

        if entry.clear_stars():  # Re-use clear_stars logic
            if entry.is_posted:
                if config.delete_if_unstarred:
                    await self._delete_starboard_post(entry, config)
                else:
                    await self._update_starboard_post(entry, config)
                    await self._save_starred_message_entry(entry)
            else:
                await self._save_starred_message_entry(entry)

    @commands.Cog.listener("on_raw_message_delete")
    async def handle_message_delete(self, payload: discord.RawMessageDeleteEvent):
        # initial checks
        if not payload.guild_id: return
        config = await self.config_cog.get_guild_config(payload.guild_id)
        if not config.starboard_channel_id: return

        entry = await self._get_starred_message_entry(payload.guild_id, payload.message_id)
        if entry and entry.is_posted:
            await self._delete_starboard_post(entry, config)

        await self._delete_starred_message_entry(payload.guild_id, payload.message_id)

    @commands.Cog.listener("on_raw_bulk_message_delete")
    async def handle_bulk_message_delete(self, payload: discord.RawBulkMessageDeleteEvent):
        # initial checks.
        if not payload.guild_id: return
        config = await self.config_cog.get_guild_config(payload.guild_id)
        if not config.starboard_channel_id: return
        if self.starred_messages_collection is None: return

        filter_query = {
            "guild_id": payload.guild_id, "original_message_id": {"$in": payload.message_ids}, "is_posted": True
        }
        affected_entries_cursor = self.starred_messages_collection.find(filter_query)
        entries_to_delete_sb_msg = [StarredMessage(**doc) async for doc in affected_entries_cursor]

        delete_tasks = [self._delete_starboard_post(entry, config) for entry in entries_to_delete_sb_msg]
        await asyncio.gather(*delete_tasks, return_exceptions=True)

        delete_filter = {
            "guild_id": payload.guild_id, "original_message_id": {"$in": payload.message_ids}
        }
        await self.starred_messages_collection.delete_many(delete_filter)
        self.logger.info(f"Cleaned up starboard DB entries for {len(payload.message_ids)} bulk deleted messages in guild {payload.guild_id}")


# --- Cog Setup ---
async def setup(bot: AssistantBot):
    if not MONGO_URI:
        bot.logger.warning("[Starboard Core] Not loading cog because MONGO_URI is not set.")
        return
    cog = StarboardCoreCog(bot)
    await bot.add_cog(cog)
    await cog._ensure_indexes()
