from datetime import datetime, timezone
from typing import Optional

import disnake


def relative_time(timestamp: datetime | int) -> str:
    """Returns a relative time from a given timestamp"""
    if not timestamp:
        return ""
    return f"<t:{int(timestamp.timestamp())}:R>" if isinstance(timestamp, datetime) else f"<t:{timestamp}:R>"


def long_date(timestamp: datetime | int) -> str:
    """Returns a long date from a given timestamp"""
    if not timestamp:
        return ""
    return f"<t:{int(timestamp.timestamp())}:D>" if isinstance(timestamp, datetime) else f"<t:{timestamp}:D>"


def time_delta(time: datetime) -> str:
    """Converts a time delta to a human readable format"""
    if not time:
        return ""
    delta = datetime.now(timezone.utc) - time
    if delta.days > 0:
        return f"{delta.days}days"
    if delta.seconds > 3600:
        return f"{delta.seconds // 3600}hrs {delta.seconds % 3600 // 60}mins"
    if delta.seconds > 60:
        return f"{delta.seconds // 60}min {delta.seconds % 60}secs"
    return f"{delta.seconds}s"


def human_bytes(_bytes: int) -> str:
    """Converts bytes to Human Readable format"""
    for x in ["bytes", "KB", "MB", "GB", "TB"]:
        if _bytes < 1024.0:
            return f"{_bytes:.2f} {x}"
        _bytes /= 1024.0


def human_int(num) -> str:
    """Convert Integers to Human readable formats."""
    for x in ["", "K", "M", "B", "T"]:
        if num < 1000:
            return f"{num:.1f} {x}"
        num /= 1000


def colour_gen(any_id: int, as_hex: Optional[bool] = False) -> [disnake.Colour | int]:
    """Generates a discord colour based on an ID"""
    r = int(any_id / 420 % 255)
    g = int(any_id / 69 / 69 % 255)
    b = int(any_id / 420 / 420 % 255)
    return disnake.Color.from_rgb(r, g, b) if not as_hex else int(f"0x{r:02x}{g:02x}{b:02x}", 16)
