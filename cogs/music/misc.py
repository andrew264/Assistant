import json


def human_format(num):
    """Convert Integers to Human readable formats."""
    num = float("{:.3g}".format(num))
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return "{}{}".format("{:f}".format(num).rstrip("0").rstrip("."), ["", "K", "M", "B", "T"][magnitude])


def AddTagstoJSON(video_id: str, tag: str):
    """Add Tags to Videos for Search"""
    with open("data/MusicCache.json", "r+") as jsonFile:
        data: dict = json.load(jsonFile)
        data[video_id]["Tags"].append(tag.lower())
        jsonFile.seek(0)
        json.dump(data, jsonFile, indent=4, sort_keys=True)
        jsonFile.close()
