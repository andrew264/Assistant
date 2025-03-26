import datetime
import uuid
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class Reminder(BaseModel):
    user_id: int
    target_user_id: Optional[int] = None
    channel_id: int
    guild_id: int
    message: str
    trigger_time: datetime.datetime
    creation_time: datetime.datetime
    reminder_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    is_dm: bool = True
    title: Optional[str] = None
    recurrence: Optional[str] = None  # "daily", "weekly", "monthly", None
    last_triggered: Optional[datetime.datetime] = None
    is_active: bool = True  # For pausing/activating reminders

    @classmethod
    @field_validator("trigger_time", "creation_time", mode="before")
    def ensure_utc(cls, v: datetime.datetime) -> datetime.datetime:
        if v.tzinfo is None:  # Assume naive times are in UTC
            return v.replace(tzinfo=datetime.timezone.utc)
        return v.astimezone(datetime.timezone.utc)
