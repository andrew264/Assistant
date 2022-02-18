import disnake

from .converters import time_delta


def available_clients(member: disnake.Member) -> str:
    """Returns a string of available clients for a Member"""
    clients = []
    if member.desktop_status.name != "offline":
        clients.append("Desktop")
    if member.mobile_status.name != "offline":
        clients.append("Mobile")
    if member.web_status.name != "offline":
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


def custom_activity(activity: disnake.CustomActivity, with_time: bool = False) -> str:
    """Returns a string of a CustomActivity"""
    value: str = ""
    if activity.emoji is not None:
        value += f"[{activity.emoji}]({activity.emoji.url}) "
    if activity.name is not None:
        value += f"{activity.name}"
    if with_time:
        value += f"\n{time_delta(activity.created_at)}"
    return value


def all_activities(member: disnake.Member, with_time: bool = False) -> dict[str, str | None]:
    """
    Returns a dictionary of all activities for a Member
    with the key being the activity type and the value being the activity
    set with_time to True to include the time the activity was created
    """
    activities = {"Status": None, "Playing": None,
                  "Streaming": None, "Spotify": None, }
    for _activity in member.activities:
        if isinstance(_activity, disnake.CustomActivity):
            activities["Status"] = custom_activity(_activity, with_time)

        elif isinstance(_activity, disnake.Game):
            activities["Playing"] =\
                f"{_activity.name}\n**{time_delta(_activity.created_at)}**" if with_time else f"{_activity.name}"

        elif isinstance(_activity, disnake.Streaming):
            activities["Streaming"] = f"[{_activity.name}]({_activity.url})"

        elif isinstance(_activity, disnake.Spotify):
            activities["Spotify"] =\
                f"Listening to [{_activity.title}]({_activity.track_url} \"by {', '.join(_activity.artists)}\")"

        elif isinstance(_activity, disnake.Activity):
            activities[_activity.type.name.capitalize()] =\
                f"{_activity.name}\n**{time_delta(_activity.created_at)}**" if with_time else f"{_activity.name}"

    return activities
