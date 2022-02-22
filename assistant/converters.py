from datetime import datetime, timezone

import disnake


def time_delta(timestamp: datetime) -> str:
    """Returns a human readable time delta"""
    if not timestamp:
        return ""
    delta = datetime.now(timezone.utc) - timestamp
    if delta.days > 0:
        return f"({delta.days} days ago)"
    if delta.seconds > 3600:
        return f"({delta.seconds // 3600}hrs {(delta.seconds // 60) % 60}mins)"
    if delta.seconds > 60:
        return f"({delta.seconds // 60}mins {delta.seconds % 60}secs)"
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


def colour_gen(any_id: int) -> disnake.Colour:
    """Generates a discord colour based on an ID"""
    r = int(any_id % 255)
    g = int(any_id / 255 % 255)
    b = int(any_id / 255 / 255 % 255)
    return disnake.Color.from_rgb(r, g, b)