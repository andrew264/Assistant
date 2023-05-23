import asyncio
from typing import Optional

import disnake
from disnake.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient

from assistant import Client
from config import mongo_uri


class Introduction(commands.Cog):
    def __init__(self, client: Client):
        self.client = client
        self.mongo_db: Optional[AsyncIOMotorClient] = None

    @commands.slash_command(description="Introduce Yourself to Others.")
    async def introduce(self, inter: disnake.ApplicationCommandInteraction, ) -> None:
        await inter.response.send_modal(title="Add Introduction",
                                        custom_id="assistant:add_intro",
                                        components=[disnake.ui.TextInput(label="Introduce Yourself",
                                                                         placeholder="I am a big pussy",
                                                                         custom_id="introduction",
                                                                         style=disnake.TextInputStyle.long,
                                                                         min_length=5, max_length=512, ), ]
                                        )
        try:
            modal_inter: disnake.ModalInteraction = await self.client.wait_for(
                "modal_submit",
                check=lambda i: i.custom_id == "assistant:add_intro" and i.author.id == inter.author.id,
                timeout=120, )
        except asyncio.TimeoutError:
            return
        await self._add_description(inter.author.id, modal_inter.text_values['introduction'])
        await modal_inter.response.send_message("Introduction Added.", ephemeral=True)
        self.client.logger.info(f"{inter.author}: Added introduction {modal_inter.text_values['introduction']}")

    async def _add_description(self, user_id: int, message: str) -> None:
        if not self.mongo_db:
            self.mongo_db = self.client.connect_to_mongo()
        db = self.mongo_db["assistant"]
        collection = db["allUsers"]

        await collection.update_one({"_id": user_id}, {"$set": {"about": message}}, upsert=True)


def setup(bot):
    if mongo_uri:
        bot.add_cog(Introduction(bot))
    else:
        bot.logger.warning("Database not configured, Introduction cog will not be loaded.")
