import re
from typing import List, Tuple

import disnake

from . import relative_time


def available_clients(member: disnake.Member) -> str:
    """Returns a string of available clients for a Member"""
    clients = []
    if str(member.desktop_status) != "offline":
        clients.append("Desktop")
    if str(member.mobile_status) != "offline":
        clients.append("Mobile")
    if str(member.web_status) != "offline":
        clients.append("Web")
    value = ', '.join(clients)
    if member.raw_status == "online":
        value = "Online in " + value
    elif member.raw_status == "idle":
        value = "Idling in " + value
    elif member.raw_status == "dnd":
        value = value + " (DND)"
    else:
        return "Offline"
    return value


def remove_brackets(string: str) -> str:
    """Removes brackets from a string"""
    return re.sub("[\(\[].*?[\)\]]", "", string).strip()


def custom_activity(activity: disnake.CustomActivity, with_time: bool = False, with_url: bool = False) -> str:
    """Returns a string of a CustomActivity"""
    value: str = ""
    if activity.emoji is not None:
        if with_url:
            value += f"[{activity.emoji}]({activity.emoji.url}) "
        else:
            value += f"{activity.emoji} " if not activity.emoji.is_custom_emoji() else f" "
    if activity.name is not None:
        value += f"{activity.name}"
    if with_time and activity.created_at:
        value += f"\n**<t:{int(activity.created_at.timestamp())}:R>**"
    return value


def all_activities(member: disnake.Member, with_time: bool = False, with_url: bool = False,
                   include_all_activities: bool = False) -> List[Tuple[str, str]]:
    """
    Returns a dictionary of all activities for a Member
    with the key being the activity type and the value being the activity
    set with_time to True to include the time the activity was created
    """
    activities = []
    for _activity in member.activities:
        if isinstance(_activity, disnake.CustomActivity):
            activities.append(("Status", custom_activity(_activity, with_time, with_url)))

        elif isinstance(_activity, disnake.Game):
            _value = f"{_activity.name}\n**{relative_time(_activity.created_at)}**" \
                if with_time and _activity.created_at else f"{_activity.name}"
            activities.append(("Playing", _value))

        elif isinstance(_activity, disnake.Streaming):
            activities.append(("Streaming", f"{_activity.name}]({_activity.url})" if with_url else f"{_activity.name}"))

        elif isinstance(_activity, disnake.Spotify):
            _value = f"Listening to [{remove_brackets(_activity.title)}]({_activity.track_url} \"" \
                     + f" \u2022 {', '.join(_activity.artists)}\")" \
                if with_url else f"Listening to {remove_brackets(_activity.title)}" \
                                 + f" \u2022 {', '.join(_activity.artists)}"
            activities.append(("Spotify", _value))

        elif isinstance(_activity, disnake.Activity):
            if include_all_activities:
                _value = f"{_activity.name}\n" + f"**<t:{int(_activity.created_at.timestamp())}:R>**" \
                    if with_time and _activity.created_at else f"{_activity.name}"
                activities.append((str(_activity.type.name).capitalize(), _value))

    return activities
