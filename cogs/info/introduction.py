import asyncio
from typing import Optional

import aiosqlite
import disnake
from disnake.ext import commands

from assistant import Client
from config import database_path


class Introduction(commands.Cog):
    def __init__(self, client: Client):
        self.client = client
        self.db: Optional[aiosqlite.Connection] = None

    @commands.slash_command(description="Introduce Yourself to Others.")
    async def introduce(self, inter: disnake.ApplicationCommandInteraction, ) -> None:
        await inter.response.send_modal(title="Add Introduction",
                                        custom_id="add_intro",
                                        components=[disnake.ui.TextInput(label="Introduce Yourself",
                                                                         placeholder="I am a big pussy",
                                                                         custom_id="introduction",
                                                                         style=disnake.TextInputStyle.long,
                                                                         min_length=5, max_length=512, ), ]
                                        )
        try:
            modal_inter: disnake.ModalInteraction = await self.client.wait_for(
                "modal_submit",
                check=lambda i: i.custom_id == "add_intro" and i.author.id == inter.author.id,
                timeout=120, )
        except asyncio.TimeoutError:
            return
        await self.add_description(inter.author.id, modal_inter.text_values['introduction'])
        await modal_inter.response.send_message("Introduction Added.", ephemeral=True)
        self.client.logger.info(f"{inter.author}: Added introduction {modal_inter.text_values['introduction']}")

    async def add_description(self, user_id: int, message: str) -> None:
        self.db = await self.client.db_connect()
        async with self.db.execute("SELECT * FROM Members WHERE USERID = ?", (user_id,)) as cursor:
            value = await cursor.fetchone()
            if value:
                await self.db.execute("UPDATE Members SET ABOUT = ? WHERE USERID = ?", (message, user_id))
                await self.client.log(f"Updated introduction for {user_id}: {message}")
            else:
                await self.db.execute("INSERT INTO Members (USERID, ABOUT) VALUES (?,?)", (user_id, message))
                await self.client.log(f"Adding introduction for {user_id}: {message}")
            if self.db.total_changes:
                await self.db.commit()
            return


def setup(bot):
    if database_path:
        bot.add_cog(Introduction(bot))
    else:
        bot.logger.warning("Database not configured, Introduction cog will not be loaded.")
