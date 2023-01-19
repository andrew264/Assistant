import sqlite3


class Report:
    def __init__(self, values: sqlite3.Row):
        self.id: int = values["report_id"]
        self.accused_id: int = values["accused_id"]
        self.accused_name: str = values["accused_name"]
        self.reporter_id: int = values["reporter_id"]
        self.reporter_name: str = values["reporter_name"]
        self.reason: str = values["reason"]
        self.time: int = values["time"]
        self.guild_id: int = values["guild_id"]

    def __str__(self) -> str:
        return f"ID: {self.id}\t{self.reporter_name} accused {self.accused_name}"

    @property
    def timestamp(self) -> str:
        return f"<t:{self.time}:D>"

    @property
    def mention_reporter(self) -> str:
        return f"<@{self.reporter_id}>"

    @property
    def mention_accused(self) -> str:
        return f"<@{self.accused_id}>"

    @property
    def guild(self) -> int:
        return self.guild_id

    @property
    def short_reason(self) -> str:
        if len(self.reason.split('\n')) > 3:
            return '\n'.join(self.reason.split('\n')[:3]) + '\n...'
        elif len(self.reason) > 50:
            return self.reason[:50] + '...'
        else:
            return self.reason
