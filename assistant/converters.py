from datetime import datetime, timezone
from typing import Optional

import disnake


def time_delta(timestamp: datetime) -> str:
    """Returns a human readable time delta"""
    if not timestamp:
        return ""
    delta = datetime.now(timezone.utc) - timestamp
    if delta.days > 365:
        return f"({delta.days // 365}Y, {int(delta.days % 365 // 30.5)}M, {int(delta.days % 365 % 30.5)}D)"
    elif delta.days > 30.5:
        return f"({int(delta.days // 30.5)}M, {int(delta.days % 30.5)}D)"
    elif delta.days > 0:
        return f"({delta.days}D, {delta.seconds // 3600}hrs)"
    if delta.seconds > 3600:
        return f"({delta.seconds // 3600}hrs {(delta.seconds // 60) % 60}mins)"
    elif delta.seconds > 60:
        return f"({delta.seconds // 60}mins {delta.seconds % 60}secs)"
    else:
        return f"({delta.seconds} secs)"


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
