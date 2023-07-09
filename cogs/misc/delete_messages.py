from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from assistant import AssistantBot


class MessageDeleteCommands(commands.Cog):
    def __init__(self, bot: AssistantBot):
        self.bot = bot
        for command in self.build_context_menus():
            self.bot.tree.add_command(command)

    async def cog_unload(self):
        for command in self.build_context_menus():
            self.bot.tree.remove_command(command.name, type=command.type)

    def build_context_menus(self):
        return [
            app_commands.ContextMenu(
                name="Delete till here",
                callback=self.__delete_till_here,
            ),
        ]

    @app_commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def __delete_till_here(self, ctx: discord.Interaction, message: discord.Message):
        assert isinstance(message.channel, (discord.TextChannel, discord.Thread))
        await ctx.response.defer(ephemeral=True)
        msgs = await message.channel.purge(after=message)
        await ctx.edit_original_response(
            content=f"Deleted {len(msgs)} messages till {message.author.mention}'s message")
        self.bot.logger.info(
            f"[DELETE] {len(msgs)} messages in {message.guild}: #{message.channel.name} by {ctx.user.display_name}"
        )

    @app_commands.command(name="clear", description="Delete messages in a channel")
    @app_commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(manage_messages=True)
    @app_commands.describe(amount="Number of messages to delete")
    async def clear(self, ctx: discord.Interaction, amount: app_commands.Range[int, 1, 420]):
        assert isinstance(ctx.channel, (discord.TextChannel, discord.Thread))
        await ctx.response.defer(ephemeral=True)
        msgs = await ctx.channel.purge(limit=amount)
        await ctx.edit_original_response(content=f"Deleted {len(msgs)} messages in {ctx.channel.mention}")
        self.bot.logger.info(
            f"[DELETE] {len(msgs)} messages in {ctx.guild}: #{ctx.channel.name} by {ctx.user.display_name}"
        )

    @commands.command(aliases=["yeet"], description="Delete messages in a channel", hidden=True)
    @commands.guild_only()
    @commands.is_owner()
    async def purge_user(self, ctx: commands.Context, user_id: Optional[int], *, content: Optional[str]) -> None:
        assert isinstance(ctx.channel, (discord.TextChannel, discord.Thread))
        await ctx.message.delete()
        if not user_id and not content:
            await ctx.send("Enter UserID or give a `Comma Seperated String` to search for")
            return
        stuff_to_delete: list[str] = [s.lower() for s in list(content.split(","))] if content else []
        if user_id:
            stuff_to_delete.append(str(user_id))

        def _mass_purge_checker(msg: discord.Message) -> bool:
            if user_id and msg.author.id == user_id:
                return True
            if any(s in str(msg.author).lower() for s in stuff_to_delete) \
                    or any(s in msg.content.lower() for s in stuff_to_delete):
                return True
            for e in msg.embeds:
                if any(s in str(e.title).lower() for s in stuff_to_delete) \
                        or any(s in str(e.description).lower() for s in stuff_to_delete) \
                        or any(s in str(e.author.name).lower() for s in stuff_to_delete) \
                        or any(s in str(e.footer.text).lower() for s in stuff_to_delete):
                    return True
                for f in e.fields:
                    if f.value and any(s in f.value.lower() for s in stuff_to_delete):
                        return True
                    if f.name and any(s in f.name.lower() for s in stuff_to_delete):
                        return True
                if e.image:
                    if any(s in str(e.image.url).lower() for s in stuff_to_delete):
                        return True
            for a in msg.attachments:
                if any(s in str(a.filename).lower() for s in stuff_to_delete):
                    return True
            return False

        deleted_msgs = await ctx.channel.purge(limit=None, check=_mass_purge_checker)
        self.bot.logger.info(
            f"[DELETE] {len(deleted_msgs)} messages in {ctx.guild}: #{ctx.channel.name} by {ctx.author.display_name}"
        )
        await ctx.send(f"Deleted {len(deleted_msgs)} messages", delete_after=30)


async def setup(bot: AssistantBot):
    await bot.add_cog(MessageDeleteCommands(bot))
