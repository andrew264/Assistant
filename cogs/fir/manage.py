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

        class DeleteReportButton(disnake.ui.Button["DeleteReportButton"]):
            _delete_report = self._delete_report

            def __init__(self, report: Report):
                super().__init__(label="Delete", style=disnake.ButtonStyle.danger)
                self.report = report

            async def callback(self, interaction: disnake.Interaction) -> None:
                await self._delete_report(self.report.id)
                await interaction.response.edit_message(content=f"{self.report.mention_reporter} 's Report deleted",
                                                        embed=None, view=None)
                self.view.stop()

        class ViewReportButton(disnake.ui.Button["ViewReportButton"]):
            def __init__(self, report: Report):
                super().__init__(style=disnake.ButtonStyle.blurple, label=f"#{report.id}", row=1)
                self.report = report

            async def callback(self, interaction: disnake.Interaction) -> None:
                report = self.report
                embed1 = disnake.Embed(title=f"Report #{report.id}", colour=disnake.Colour.red())
                embed1.add_field(name="Accused",
                                 value=report.mention_accused + f" ({report.accused_id})")
                embed1.add_field(name="Reported on", value=report.timestamp)
                embed1.add_field(name="Reason", value=report.reason, inline=False)
                embed1.set_footer(text=f"Reported by {report.reporter_name} (ID: {report.reporter_id})")
                view1 = disnake.ui.View(timeout=60).add_item(DeleteReportButton(report))
                await interaction.response.send_message(embed=embed1, view=view1, ephemeral=True)

        class ReportPageList(disnake.ui.View):
            items_per_page = 5
            _delete_report = self._delete_report

            def __init__(self, _reports: list[Report]):
                super().__init__(timeout=120)
                self.reports = _reports
                self.page = 0
                self.max_page = len(self.reports) // self.items_per_page

            async def interaction_check(self, interaction: disnake.Interaction) -> bool:
                return interaction.user == inter.author

            async def on_timeout(self) -> None:
                await inter.edit_original_message(content="View reports timed out", view=None)

            async def on_error(self, error: Exception, item: disnake.ui.Item, interaction: disnake.Interaction) -> None:
                await inter.edit_original_message(content=f"An error occurred: {error}")

            @disnake.ui.button(label="Previous", custom_id="prev", style=disnake.ButtonStyle.gray)
            async def prev(self, button: disnake.ui.Button, interaction: disnake.Interaction) -> None:
                self.page -= 1 if self.page > 0 else 0
                await interaction.response.edit_message(embed=self.embed, view=self)

            @disnake.ui.button(label="Next", custom_id="next", style=disnake.ButtonStyle.gray)
            async def next(self, button: disnake.ui.Button, interaction: disnake.Interaction) -> None:
                self.page += 1 if self.page < self.max_page else 0
                await interaction.response.edit_message(embed=self.embed, view=self)

            def update_buttons(self) -> None:
                self.children: list[disnake.ui.Button]
                for child in list(self.children):
                    if child.custom_id not in ("prev", "next"):
                        self.remove_item(child)
                if len(self.reports) <= self.items_per_page:
                    self.remove_item(self.prev)
                    self.remove_item(self.next)
                for report in self.reports[self.page * self.items_per_page: (self.page + 1) * self.items_per_page]:
                    self.add_item(ViewReportButton(report))

            @property
            def embed(self) -> disnake.Embed:
                self.update_buttons()
                embed = disnake.Embed(title=f"{user if user else inter.guild} has {len(reports)} reports",
                                      colour=disnake.Colour.blurple())
                for report in self.reports[self.page * self.items_per_page: (self.page + 1) * self.items_per_page]:
                    name = f"Report #{report.id}" if user else \
                        f"Report #{report.id} on {report.accused_name}"
                    embed.add_field(name=name,
                                    value=f"**Reason:** {report.short_reason}\n"
                                          f"**Reporter:** {report.mention_reporter}\n"
                                          f"**Time:** {report.timestamp}", inline=False)
                embed.set_footer(text=f"Page {self.page + 1}/{self.max_page + 1}")
                return embed

        if reports and is_admin:  # reports found, user is admin
            view = ReportPageList(reports)
            await inter.edit_original_message(embed=view.embed, view=view)
            return

    async def _fetch_reports(self, user: Optional[disnake.Member] = None,
                             guild_id: Optional[int] = None) -> list[Report]:
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

    async def _delete_report(self, report_id: int) -> None:
        """
        Deletes a report from the database.
        """
        self._db = await self.client.db_connect()
        await self._db.execute("DELETE FROM MEMBER_REPORTS WHERE report_id = ?", (report_id,))
        self.client.logger.info(f"Deleted report #{report_id}")
        await self._db.commit()


def setup(client: Client) -> None:
    client.add_cog(Manage(client))
