import asyncio
import datetime
from typing import Optional

import aiosqlite
import disnake
from disnake.ext import commands

from assistant import Client


class Report(commands.Cog):
    def __init__(self, client: Client):
        self.client = client
        self._db: Optional[aiosqlite.Connection] = None

    @commands.user_command(name="File a Complaint", dm_permission=False)
    async def report(self, inter: disnake.ApplicationCommandInteraction) -> None:
        if inter.author.id == inter.target.id:
            await inter.response.send_message("You can't report yourself!", ephemeral=True)
            return
        if inter.target.bot:
            await inter.response.send_message("You can't report a bot!", ephemeral=True)
            return
        user = inter.target
        await inter.response.send_modal(title="First Information Report",
                                        custom_id="fir_" + str(user),
                                        components=[disnake.ui.TextInput(
                                            label=f"Tell us about {user}",
                                            placeholder=f"The existence of {user} is bothering me",
                                            custom_id="report_reason",
                                            style=disnake.TextInputStyle.long,
                                            min_length=5, max_length=1024, ), ]
                                        )
        try:
            modal_inter: disnake.ModalInteraction = await self.client.wait_for(
                "modal_submit",
                check=lambda i: i.custom_id == "fir_" + str(user) and i.author.id == inter.author.id,
                timeout=420, )
        except asyncio.TimeoutError:
            return
        await self._add_to_db(user, modal_inter.text_values['report_reason'], inter.author)
        await modal_inter.response.send_message("Report Filed.", ephemeral=True)

    async def _add_to_db(self, user: disnake.Member, reason: str, report_by: disnake.Member) -> None:
        self._db = await self.client.db_connect()
        await self._db.execute(
            f"""INSERT INTO MEMBER_REPORTS (accused_id, accused_name, guild_id, reporter_id, reporter_name, reason)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (user.id,
             str(user),
             user.guild.id,
             report_by.id,
             str(report_by),
             reason)
        )
        if self._db.total_changes:
            await self._db.commit()


def setup(client: Client) -> None:
    client.add_cog(Report(client))
