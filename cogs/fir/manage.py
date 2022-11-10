from typing import Optional

import aiosqlite
import disnake
from disnake.ext import commands

from assistant import Client, Report


class Manage(commands.Cog):
    def __init__(self, client: Client):
        self.client = client
        self._db: Optional[aiosqlite.Connection] = None

    @commands.slash_command(name="view-reports", description="View a user's reports")
    async def view(self, inter: disnake.ApplicationCommandInteraction,
                   user: Optional[disnake.Member] = commands.Param(description="Select a user to view his reports",
                                                                   default=None)) -> None:
        is_admin = inter.channel.permissions_for(inter.author).administrator
        await inter.response.defer(ephemeral=is_admin)
        if not is_admin and inter.author != user:  # if user is not admin and not viewing his own reports
            await inter.edit_original_message(content="You can only view your own reports.")
            return
        if is_admin and user is None:
            reports = await self._fetch_reports(guild_id=inter.guild.id)
        else:
            user = user or inter.author
            reports = await self._fetch_reports(user=user)
        if not reports:  # no reports
            await inter.edit_original_message(content="No reports found")
            return
        if reports and not is_admin:  # reports found, user viewing own reports
            await inter.edit_original_message(content=f"You have {len(reports)} reports")
            return
        if reports and is_admin:  # reports found, user is admin
            embed = disnake.Embed(title=f"{user if user else inter.guild} has {len(reports)} reports")
            for report in reports:
                embed.add_field(name=str(report), value=report.short_reason, inline=False)
            await inter.edit_original_message(embed=embed)
            return

    async def _fetch_reports(self, user: Optional[disnake.Member] = None,
                             guild_id: Optional[int] = None) -> list[Report]:
        if self._db is None:
            self._db = await self.client.db_connect()
        if user is None and guild_id is None:
            raise ValueError("Must pass either user or guild_id")
        elif guild_id and user is None:
            reports = await self._db.execute(
                "SELECT * FROM MEMBER_REPORTS WHERE guild_id = ?",
                (guild_id,)
            )
        else:
            reports = await self._db.execute(
                "SELECT * FROM MEMBER_REPORTS WHERE accused_id = ? and guild_id = ?",
                (user.id, user.guild.id))
        return [Report(val) for val in await reports.fetchall()]


def setup(client: Client) -> None:
    client.add_cog(Manage(client))
