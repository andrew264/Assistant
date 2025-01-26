import asyncio
from enum import Enum
from functools import partial
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands
from googletrans import Translator

from assistant import AssistantBot


class Language(Enum):
    ENGLISH = "en"
    JAPANESE = "ja"
    TAMIL = "ta"
    HINDI = "hi"
    SPANISH = "es"
    FRENCH = "fr"


class TranslatorProMax(commands.Cog):
    def __init__(self, bot: AssistantBot):
        self.bot = bot
        for command in self.build_context_menus():
            self.bot.tree.add_command(command)

    async def cog_unload(self):
        for command in self.build_context_menus():
            self.bot.tree.remove_command(command.name, type=command.type)

    async def get_webhook(self, _id: int) -> Optional[discord.Webhook]:
        channel = self.bot.get_channel(_id)
        assert isinstance(channel, (discord.TextChannel, discord.Thread))
        webhooks = await channel.webhooks()
        for w in webhooks:
            if w.name == "Assistant":
                return w
        else:
            return await channel.create_webhook(name="Assistant", avatar=await self.bot.user.display_avatar.read())

    @staticmethod
    async def trans_fn(text: str, language: Language, pronounce: bool = True) -> str:
        loop = asyncio.get_event_loop()
        t_fn = partial(Translator().translate, text=text, dest=str(language.value))
        translation = await loop.run_in_executor(None, t_fn)
        return translation.pronunciation if pronounce else translation.text

    def build_context_menus(self):
        return [app_commands.ContextMenu(name="Translate to English", callback=self.trans_msg_command, ), ]

    @app_commands.guild_only()
    async def trans_msg_command(self, ctx: discord.Interaction, message: discord.Message):
        await ctx.response.defer(ephemeral=True)
        translated = await self.trans_fn(message.clean_content, Language.ENGLISH, pronounce=False)
        await ctx.edit_original_response(content=translated)

    @app_commands.command(name='translate', description='Translate Text')
    @app_commands.describe(sentence='The sentence to translate', language='The language to translate to', pronunciation='Pronounce the translation')
    async def trans_command(self, ctx: discord.Interaction, sentence: str = '', language: Language = Language.ENGLISH, pronunciation: bool = True):
        await ctx.response.send_message(content="Translating...", ephemeral=True)
        translated = await self.trans_fn(sentence, language, pronunciation)
        webhook = await self.get_webhook(ctx.channel_id)
        await webhook.send(translated, username=ctx.user.display_name, avatar_url=ctx.user.display_avatar.url)


async def setup(bot: AssistantBot):
    await bot.add_cog(TranslatorProMax(bot))
