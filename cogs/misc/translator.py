from enum import Enum
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands
from googletrans import Translator

from assistant import AssistantBot


class Language(Enum):
    ENGLISH = "en"
    JAPANESE = "ja"
    JAP_ENGLISH = "jp"
    TAMIL = "ta"
    THANGLISH = "ta"
    SPANISH = "es"


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
    def _translate(text: str, language: Language) -> str:
        pronounce = False
        if Language in (Language.JAPANESE, Language.THANGLISH):
            pronounce = True
        translation = Translator().translate(text, dest=language.value)
        return translation.text if not pronounce else translation.pronunciation

    def build_context_menus(self):
        return [
            app_commands.ContextMenu(
                name="Translate to English",
                callback=self.__translate_msg_command,
            ),
        ]

    @app_commands.guild_only()
    async def __translate_msg_command(self, ctx: discord.Interaction, message: discord.Message):
        await ctx.defer(ephemeral=True)
        translated = self._translate(message.clean_content(), Language.ENGLISH)
        await ctx.edit_original_response(content=translated)

    @app_commands.command(name='send', description='Translate Text')
    @app_commands.describe(sentence='The sentence to translate')
    async def trans_command(self, ctx: discord.Interaction, sentence: str = '', language: Language = Language.ENGLISH):
        await ctx.defer(ephemeral=True)
        translated = self._translate(sentence, language)
        await ctx.edit_original_response(content="Sent!")
        webhook = await self.get_webhook(ctx.channel_id)
        await webhook.send(translated, username=ctx.user.display_name, avatar_url=ctx.user.display_avatar.url)


async def setup(bot: AssistantBot):
    await bot.add_cog(TranslatorProMax(bot))
