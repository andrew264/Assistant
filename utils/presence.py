import re
from typing import Tuple, List

import discord
from discord import utils


def available_clients(member: discord.Member) -> str:
    """Returns a string of available clients for a Member"""
    if member.raw_status == "offline":
        return "Offline"

    clients = []
    if member.desktop_status != discord.Status.offline:
        clients.append("Desktop")
    if member.mobile_status != discord.Status.offline:
        clients.append("Mobile")
    if member.web_status != discord.Status.offline:
        clients.append("Web")

    client_str = ", ".join(clients)

    match member.raw_status:
        case "online":
            value = f"Online in {client_str}"
        case "idle":
            value = f"Idling in {client_str}"
        case "dnd":
            value = f"{client_str} (DND)"
        case _:
            value = f"{member.raw_status} in {client_str}"

    return value


def custom_activity(activity: discord.CustomActivity, with_time: bool = False, with_url: bool = False) -> str:
    """Returns a string of a CustomActivity"""
    value: str = ""
    if activity.emoji is not None:
        if with_url and activity.emoji.is_custom_emoji():
            value += f"[{activity.emoji}]({activity.emoji.url}) "
        else:
            value += f"{activity.emoji} "
    if activity.name is not None:
        value += f"{activity.name}"
    if with_time and activity.created_at:
        value += f"\n**<t:{int(activity.created_at.timestamp())}:R>**"
    return value.strip()


def remove_brackets(string: str) -> str:
    """Removes brackets from a string"""
    return re.sub(r"[(\[].*?[)\]]", "", string).strip()


def all_activities(member: discord.Member, with_time: bool = False, with_url: bool = False,
                   include_all_activities: bool = False) -> dict[str, str]:
    """
    Returns a dictionary of all activities for a Member
    with the key being the activity type and the value being the activity string.

    Args:
        member: The discord.Member to get activities from.
        with_time: Whether to include the time the activity was created.
        with_url: Whether to include URLs in the activity string (if applicable).
        include_all_activities: Whether to include all activities of type discord.Activity.
    """
    activities: dict[str, str] = {}

    for _activity in member.activities:
        if isinstance(_activity, discord.CustomActivity):
            activities["Custom Status"] = custom_activity(_activity, with_time, with_url)

        elif isinstance(_activity, discord.Game):
            value = f"{_activity.name}\n**{utils.format_dt(_activity.created_at, 'R')}**" if with_time and _activity.created_at else f"{_activity.name}"
            activities["Playing"] = value

        elif isinstance(_activity, discord.Streaming):
            value = f"{_activity.name}]({_activity.url})" if with_url else f"{_activity.name}"
            activities["Streaming"] = value

        elif isinstance(_activity, discord.Spotify):
            value = f"Listening to [{remove_brackets(_activity.title)}]({_activity.track_url}) by {', '.join(_activity.artists)}" \
                if with_url else f"Listening to {remove_brackets(_activity.title)} \u2022 {', '.join(_activity.artists)}"
            activities["Spotify"] = value

        elif isinstance(_activity, discord.Activity) and include_all_activities:
            value = f"{_activity.name}\n" + f"**<t:{int(_activity.created_at.timestamp())}:R>**" if with_time and _activity.created_at else f"{_activity.name}"
            activities[str(_activity.type.name).capitalize()] = value

    return activities
