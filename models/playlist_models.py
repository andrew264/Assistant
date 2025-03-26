from datetime import datetime
from typing import List, Optional

import discord
from pydantic import BaseModel, Field, field_validator


class Song(BaseModel):
    title: str
    artist: str
    uri: str
    duration: float
    thumbnail: Optional[str] = None
    source: str

    @classmethod
    @field_validator("source", mode="before")
    def set_source(cls, v, values):
        # Simple logic: if YouTube in URI, mark as youtube
        return 'youtube' if 'youtube' in values.get('uri', '') else v or 'other'


class PlaylistModel(BaseModel):
    user_id: int
    guild_id: int
    name: str = Field(..., max_length=32)
    songs: List[Song] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=discord.utils.utcnow)
    updated_at: datetime = Field(default_factory=discord.utils.utcnow)

    @classmethod
    @field_validator("name")
    def validate_name(cls, v):
        if len(v) > 32:
            raise ValueError("Playlist name is too long (max 32 characters)")
        return v
