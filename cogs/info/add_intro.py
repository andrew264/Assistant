import traceback
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient

from assistant import AssistantBot
from config import MONGO_URI


class Introduction(commands.Cog):
    def __init__(self, bot: AssistantBot):
        self.bot = bot
        self.mongo: Optional[AsyncIOMotorClient] = None

    async def setup_hook(self):
        self.mongo = self.bot.connect_to_mongo()

    @app_commands.command(name="introduce", description="Introduce yourself to other members of the server")
    async def introduce(self, ctx: discord.Interaction):
        modal = discord.ui.Modal(title="Introduction", timeout=300, )
        modal.add_item(discord.ui.TextInput(label="Introduce yourself", placeholder="I am a big pussy", style=discord.TextStyle.paragraph, min_length=8, max_length=1024))
        modal.on_submit = self._on_submit
        await ctx.response.send_modal(modal)

    async def _on_submit(self, interaction: discord.Interaction):
        try:
            intro: str = interaction.data['components'][0]['components'][0]['value']
            self.bot.logger.info(f"[INTRO ADDED] {interaction.user.display_name}: {intro}")
            await self._add_intro_to_db(interaction.user.id, intro)
            await interaction.response.send_message("Introduction added successfully", ephemeral=True)
        except Exception as e:
            self.bot.logger.error(f"Error while adding intro: {e}")
            traceback.print_exc()
            await interaction.response.send_message("Error while adding introduction", ephemeral=True)

    async def _add_intro_to_db(self, user_id: int, intro: str):
        if not self.mongo:
            self.mongo = self.bot.connect_to_mongo()
        db = self.mongo["assistant"]
        collection = db["allUsers"]

        await collection.update_one({"_id": user_id}, {"$set": {"about": intro}}, upsert=True)


async def setup(bot: AssistantBot):
    if MONGO_URI:
        await bot.add_cog(Introduction(bot))
    else:
        bot.logger.warning("MongoDB URI not found. Introduction cog not loaded.")
