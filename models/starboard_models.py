# models/starboard_models.py
from datetime import datetime
from typing import List, Optional

import discord
from pydantic import BaseModel, Field, field_validator, validator

DEFAULT_STAR_EMOJI = "⭐"
DEFAULT_THRESHOLD = 3


class StarboardConfig(BaseModel):
    guild_id: int = Field(..., alias="_id")  # Use guild_id as the document ID
    is_enabled: bool = False
    starboard_channel_id: Optional[int] = None
    star_emoji: str = DEFAULT_STAR_EMOJI
    threshold: int = DEFAULT_THRESHOLD
    allow_self_star: bool = False
    allow_bot_messages: bool = False
    ignore_nsfw_channels: bool = True
    delete_if_unstarred: bool = False
    log_channel_id: Optional[int] = None
    created_at: datetime = Field(default_factory=discord.utils.utcnow)
    updated_at: datetime = Field(default_factory=discord.utils.utcnow)

    @classmethod
    @field_validator('threshold')
    def threshold_must_be_positive(cls, v):
        if v < 1:
            raise ValueError('Threshold must be at least 1')
        return v

    @classmethod
    @field_validator('star_emoji', mode='before')
    def validate_emoji(cls, v):
        if not v:  # Handle empty input
            return DEFAULT_STAR_EMOJI
        if v.startswith('<') and v.endswith('>'):
            parts = v.strip('<>').split(':')
            if len(parts) == 3:
                try:
                    int(parts[-1])  # Check if ID is integer
                    return v
                except ValueError:
                    raise ValueError("Invalid custom emoji format")
        return v


class StarredMessage(BaseModel):
    # Using guild_id and original_message_id as the compound key for lookups.
    guild_id: int
    original_channel_id: int
    original_message_id: int
    starboard_message_id: Optional[int] = None
    starrer_user_ids: List[int] = Field(default_factory=list)
    star_count: int = 0
    is_posted: bool = False
    last_updated: datetime = Field(default_factory=discord.utils.utcnow)
    # **MongoDB Index Required:** createIndex({ guild_id: 1, original_message_id: 1 }, { unique: true })
    # Optional Index: createIndex({ guild_id: 1, starboard_message_id: 1 })

    def update_stars(self, user_id: int, add: bool = True) -> bool:
        """Adds or removes a user ID and updates star count. Returns True if count changed."""
        original_count = self.star_count
        if add:
            if user_id not in self.starrer_user_ids:
                self.starrer_user_ids.append(user_id)
        else:
            if user_id in self.starrer_user_ids:
                self.starrer_user_ids.remove(user_id)

        new_count = len(self.starrer_user_ids)
        if new_count != self.star_count:
            self.star_count = new_count
            self.last_updated = discord.utils.utcnow()
            return True
        return False

    def clear_stars(self):
        """Resets stars. Returns True if count changed."""
        if self.star_count > 0:
            self.starrer_user_ids = []
            self.star_count = 0
            self.last_updated = discord.utils.utcnow()
            return True
        return False
