from typing import Optional

import discord
from cachetools import TTLCache
from discord import app_commands
from discord.ext import commands

from assistant import AssistantBot
from config import DATABASE_NAME, MONGO_URI
from models.starboard_models import StarboardConfig, DEFAULT_STAR_EMOJI, DEFAULT_THRESHOLD

CONFIG_CACHE_TTL = 3600  # Cache configs for 1 hour
CONFIG_CACHE_SIZE = 1000


class StarboardConfigCog(commands.Cog, name="Starboard Config"):
    """Commands to configure the starboard system."""

    def __init__(self, bot: AssistantBot):
        self.bot = bot
        self._db = self.bot.database
        self._config_cache: TTLCache = TTLCache(maxsize=CONFIG_CACHE_SIZE, ttl=CONFIG_CACHE_TTL)
        if not self._db:
            self.bot.logger.warning("[Starboard Config] MongoDB not available. Starboard will not function.")

    @property
    def collection(self):
        if not self._db: return None
        return self._db[DATABASE_NAME]["starboard_configs"]

    async def get_guild_config(self, guild_id: int) -> StarboardConfig:
        """Gets StarboardConfig for a guild, checks cache first."""
        if guild_id in self._config_cache:
            return self._config_cache[guild_id]

        if self.collection is None:
            # Return default config if DB is unavailable
            return StarboardConfig(_id=guild_id)

        config_data = await self.collection.find_one({"_id": guild_id})
        if config_data:
            config = StarboardConfig(**config_data)
        else:
            config = StarboardConfig(_id=guild_id)
        self._config_cache[guild_id] = config
        return config

    async def _update_config(self, config: StarboardConfig):
        """Updates config in DB and cache."""
        config.updated_at = discord.utils.utcnow()
        if self.collection is not None:
            await self.collection.update_one({"_id": config.guild_id}, {"$set": config.model_dump(exclude={'guild_id', 'created_at'}, by_alias=False)}, upsert=True)
        # Update cache
        self._config_cache[config.guild_id] = config
        self.bot.logger.info(f"[Starboard Config] Updated config for guild {config.guild_id}")

    # --- Slash Commands ---
    starboard_group = app_commands.Group(name="starboard", description="Manage the starboard settings.", default_permissions=discord.Permissions(manage_guild=True))

    async def cog_app_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError) -> None:
        self.bot.logger.error(f'Error in playlist command: {error}', exc_info=True)
        await interaction.edit_original_response(content=f"An error occurred while executing this command.\n```py\n{error}\n```")

    @starboard_group.command(name="enable", description="Enable the starboard system for this server.")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def enable(self, interaction: discord.Interaction):
        if self.collection is None:
            return await interaction.response.send_message("Database not available.", ephemeral=True)
        await interaction.response.defer(ephemeral=True)
        config = await self.get_guild_config(interaction.guild_id)
        if not config.starboard_channel_id:
            return await interaction.edit_original_response(content="Please set a starboard channel first using `/starboard channel set`.")
        if config.is_enabled:
            return await interaction.edit_original_response(content="Starboard is already enabled.")

        config.is_enabled = True
        await self._update_config(config)
        await interaction.edit_original_response(content="✅ Starboard has been enabled.")

    @starboard_group.command(name="disable", description="Disable the starboard system for this server.")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def disable(self, interaction: discord.Interaction):
        if self.collection is None:
            return await interaction.response.send_message("Database not available.", ephemeral=True)
        await interaction.response.defer(ephemeral=True)
        config = await self.get_guild_config(interaction.guild_id)
        if not config.is_enabled:
            return await interaction.edit_original_response(content="Starboard is already disabled.")

        config.is_enabled = False
        await self._update_config(config)
        await interaction.edit_original_response(content="❌ Starboard has been disabled.")

    @starboard_group.command(name="channel", description="Set or remove the starboard channel.")
    @app_commands.describe(channel="The channel to use for starboard posts (leave empty to remove).")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def channel(self, interaction: discord.Interaction, channel: Optional[discord.TextChannel] = None):
        if self.collection is None:
            return await interaction.response.send_message("Database not available.", ephemeral=True)
        await interaction.response.defer(ephemeral=True)
        config = await self.get_guild_config(interaction.guild_id)

        if channel:
            perms = channel.permissions_for(interaction.guild.me)
            if not (perms.send_messages and perms.embed_links and perms.attach_files and perms.read_message_history):
                return await interaction.edit_original_response(
                    content=f"I lack necessary permissions in {channel.mention} (Need Send Messages, Embed Links, Attach Files, Read History).")

            config.starboard_channel_id = channel.id
            await self._update_config(config)
            await interaction.edit_original_response(content=f"Starboard channel set to {channel.mention}.")
        else:
            config.starboard_channel_id = None
            config.is_enabled = False
            await self._update_config(config)
            await interaction.edit_original_response(content="Starboard channel removed. Starboard is now disabled.")

    @starboard_group.command(name="emoji", description="Set the emoji used for starring messages.")
    @app_commands.describe(emoji=f"The emoji to use (default is {DEFAULT_STAR_EMOJI}). Custom emojis supported.")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def emoji(self, interaction: discord.Interaction, emoji: str):
        if self.collection is None:
            return await interaction.response.send_message("Database not available.", ephemeral=True)
        await interaction.response.defer(ephemeral=True)
        config = await self.get_guild_config(interaction.guild_id)

        # Try validating the emoji
        try:
            # Re-use the Pydantic validator logic
            validated_emoji = StarboardConfig.validate_emoji(emoji)
            # Attempt to fetch custom emoji if applicable
            if validated_emoji.startswith('<'):
                emoji_id = int(validated_emoji.split(':')[-1].strip('>'))
                guild_emoji = await interaction.guild.fetch_emoji(emoji_id)
                if not guild_emoji:
                    raise ValueError("Custom emoji not found in this server.")
        except ValueError as e:
            return await interaction.edit_original_response(content=f"Invalid emoji provided: {e}")
        except discord.HTTPException:
            return await interaction.edit_original_response(content="Could not verify the custom emoji.")

        config.star_emoji = validated_emoji
        await self._update_config(config)
        await interaction.edit_original_response(content=f"Star emoji set to {config.star_emoji}.")

    @starboard_group.command(name="threshold", description="Set the minimum stars needed to post a message.")
    @app_commands.describe(count=f"The number of unique reactions required (default: {DEFAULT_THRESHOLD}, min: 1).")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def threshold(self, interaction: discord.Interaction, count: app_commands.Range[int, 1, None]):
        if self.collection is None:
            return await interaction.response.send_message("Database not available.", ephemeral=True)
        await interaction.response.defer(ephemeral=True)
        config = await self.get_guild_config(interaction.guild_id)
        config.threshold = count
        await self._update_config(config)
        await interaction.edit_original_response(content=f"Star threshold set to {count}.")

    @starboard_group.command(name="settings", description="Show or toggle current starboard settings.")
    @app_commands.describe(setting="The setting to toggle (optional).")
    @app_commands.choices(setting=[app_commands.Choice(name="Allow Self Star", value="allow_self_star"), app_commands.Choice(name="Allow Bot Messages", value="allow_bot_messages"),
        app_commands.Choice(name="Ignore NSFW Channels", value="ignore_nsfw_channels"),
        app_commands.Choice(name="Delete if Unstarred Below Threshold", value="delete_if_unstarred"), ])
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def settings(self, interaction: discord.Interaction, setting: Optional[app_commands.Choice[str]] = None):
        if self.collection is None:
            return await interaction.response.send_message("Database not available.", ephemeral=True)
        await interaction.response.defer(ephemeral=True)
        config = await self.get_guild_config(interaction.guild_id)

        if setting:
            setting_name = setting.value
            current_value = getattr(config, setting_name)
            new_value = not current_value
            setattr(config, setting_name, new_value)
            await self._update_config(config)
            await interaction.edit_original_response(content=f"{setting.name} has been set to {'✅ Enabled' if new_value else '❌ Disabled'}.")
        else:
            # Show current settings
            embed = discord.Embed(title="Starboard Settings", color=discord.Color.blue(), )
            embed.add_field(name="Status", value='✅ Enabled' if config.is_enabled else '❌ Disabled', inline=True)
            starboard_ch = self.bot.get_channel(config.starboard_channel_id) if config.starboard_channel_id else None
            embed.add_field(name="Channel", value=starboard_ch.mention if starboard_ch else 'Not Set', inline=True)
            embed.add_field(name="Emoji", value=config.star_emoji, inline=True)
            embed.add_field(name="Threshold", value=str(config.threshold), inline=True)
            embed.add_field(name="Allow Self Star", value='✅ Yes' if config.allow_self_star else '❌ No', inline=True)
            embed.add_field(name="Allow Bot Messages", value='✅ Yes' if config.allow_bot_messages else '❌ No', inline=True)
            embed.add_field(name="Ignore NSFW", value='✅ Yes' if config.ignore_nsfw_channels else '❌ No', inline=True)
            embed.add_field(name="Delete if Unstarred", value='✅ Yes' if config.delete_if_unstarred else '❌ No', inline=True)
            log_ch = self.bot.get_channel(config.log_channel_id) if config.log_channel_id else None
            embed.add_field(name="Log Channel", value=log_ch.mention if log_ch else 'Not Set', inline=True)
            embed.add_field(name=f"Last updated:", value=f"{discord.utils.format_dt(config.updated_at, 'R')}", inline=False)
            await interaction.edit_original_response(embed=embed)


async def setup(bot: AssistantBot):
    if not MONGO_URI:
        bot.logger.warning("[Starboard Config] Not loading cog because MONGO_URI is not set.")
        return
    await bot.add_cog(StarboardConfigCog(bot))
