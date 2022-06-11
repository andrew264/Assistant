import re

import disnake

from .converters import relative_time


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
    return re.sub("[\(\[].*?[\)\]]", "", string)


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
    if with_time:
        value += f"\n**<t:{int(activity.created_at.timestamp())}:R>**"
    return value


def all_activities(member: disnake.Member, with_time: bool = False, with_url: bool = False) -> dict[str, str | None]:
    """
    Returns a dictionary of all activities for a Member
    with the key being the activity type and the value being the activity
    set with_time to True to include the time the activity was created
    """
    activities = {"Status": None, "Playing": None,
                  "Streaming": None, "Spotify": None, }
    for _activity in member.activities:
        if isinstance(_activity, disnake.CustomActivity):
            activities["Status"] = custom_activity(_activity, with_time, with_url)

        elif isinstance(_activity, disnake.Game):
            activities["Playing"] = \
                f"{_activity.name}\n**{relative_time(_activity.created_at)}**" if with_time else f"{_activity.name}"

        elif isinstance(_activity, disnake.Streaming):
            activities["Streaming"] = f"[{_activity.name}]({_activity.url})" if with_url else f"{_activity.name}"

        elif isinstance(_activity, disnake.Spotify):
            activities["Spotify"] = \
                f"Listening to [{remove_brackets(_activity.title)}]({_activity.track_url} \"by {', '.join(_activity.artists)}\")" \
                    if with_url else f"Listening to {remove_brackets(_activity.title)} by {', '.join(_activity.artists)}"

        elif isinstance(_activity, disnake.Activity):
            if activities["Playing"] is None:
                activities[str(_activity.type).capitalize()] = \
                    f"{_activity.name}\n**<t:{int(_activity.created_at.timestamp())}:R>**" if with_time else f"{_activity.name}"
            else:
                activities["Also Playing"] = \
                    f"{_activity.name}\n**<t:{int(_activity.created_at.timestamp())}:R>**" if with_time else f"{_activity.name}"

    return activities
