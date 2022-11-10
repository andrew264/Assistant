import sqlite3


class Report:
    def __init__(self, values: sqlite3.Row):
        self.report_id: int = values[0]
        self.accused_id: int = values[1]
        self.accused_name: str = values[2]
        self.reporter_id: int = values[3]
        self.reporter_name: str = values[4]
        self.reason: str = values[5]
        self.time: int = values[6]
        self.guild_id: int = values[7]

    def __str__(self) -> str:
        return f"ID: {self.report_id}\t{self.reporter_name} accused {self.accused_name}"

    @property
    def timestamp(self) -> str:
        return f"<t:{self.time}:R>"

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
        return self.reason[:100] + "..." if len(self.reason) > 100 else self.reason
