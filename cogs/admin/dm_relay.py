import re
from typing import Optional, Union, List

import discord
from discord.ext import commands

from assistant import AssistantBot
from config import DM_RECIPIENTS_CATEGORY, OWNER_ID

rx_url = re.compile(r"(?P<url>https?://\S+)")


class DMRelay(commands.Cog):
    def __init__(self, bot: AssistantBot):
        self.bot = bot

    async def get_webhook(self, user: Union[discord.User, discord.Member]) -> Optional[discord.Webhook]:
        assert self.bot.user
        category = self.bot.get_channel(DM_RECIPIENTS_CATEGORY)
        assert isinstance(category, discord.CategoryChannel)
        if not category:
            return None
        for channel in category.channels:
            if isinstance(channel, discord.TextChannel) and channel.topic and str(user.id) in channel.topic:
                for webhook in await channel.webhooks():
                    assert webhook.user
                    assert self.bot.user
                    if webhook.user.id == self.bot.user.id:
                        return webhook
                else:
                    return await channel.create_webhook(name=f"Assistant",
                                                        avatar=await self.bot.user.display_avatar.read())
        else:
            channel = await category.create_text_channel(name=f"{user.name}", topic=f"USERID:{user.id}")
            return await channel.create_webhook(name=f"Assistant", avatar=await self.bot.user.display_avatar.read())

    @commands.Cog.listener('on_message')
    async def dm_listener(self, message: discord.Message):
        if message.guild or message.author.bot:
            return
        self.bot.logger.info(f"[NEW DM] from {message.author} ({message.author.id}): {message.content}")
        if not DM_RECIPIENTS_CATEGORY:
            return await message.channel.send("Sorry, I can't DM you right now. Please try again later.")
        webhook = await self.get_webhook(message.author)
        if not webhook:
            return await message.channel.send("Sorry, I can't DM you right now. Please try again later.")

        msg_content = f"MSGID:{message.id}\n\n"
        if message.reference and isinstance(message.reference.resolved, discord.Message):
            msg_content += f"- Replying to: `{message.reference.resolved.content[:100]}`\n"
        if message.content:
            msg_content += f"- Content:\n```{message.content}```\n"
        # check if content match url pattern regex
        if message.content and rx_url.match(message.content):
            urlmatch = rx_url.match(message.content)
            if urlmatch:
                url = urlmatch.group("url")
                msg_content += f"URL: {url}\n"
        msg_content += "-" * 100 + "\n"
        files: List[discord.File] = [await attachment.to_file() for attachment in message.attachments]
        await webhook.send(content=msg_content, files=files,
                           username=message.author.display_name, avatar_url=message.author.display_avatar.url)
        await message.add_reaction("✅")

    @commands.Cog.listener('on_message_edit')
    async def dm_edit_listener(self, before: discord.Message, after: discord.Message):
        if before.guild or before.author.bot:
            return
        self.bot.logger.info(f"[EDITED DM] from {before.author} ({before.author.id}): {after.content}")
        if not DM_RECIPIENTS_CATEGORY:
            return await before.channel.send("Sorry, I can't DM you right now. Please try again later.")
        webhook = await self.get_webhook(after.author)
        if not webhook:
            return await before.channel.send("Sorry, I can't DM you right now. Please try again later.")

        msg_content = f"MSGID:{after.id}\n\n"
        if after.reference and isinstance(after.reference.resolved, discord.Message):
            msg_content += f"- Replying to: `{after.reference.resolved.content[:100]}`\n"
        if before.content:
            msg_content += f"- Original Message:\n```{before.content}```\n"
        if after.content:
            msg_content += f"- Updated Message:\n```{after.content}```\n"
        # check if content match url pattern regex
        if after.content and rx_url.match(after.content):
            urlmatch = rx_url.match(after.content)
            if urlmatch:
                url = urlmatch.group("url")
                msg_content += f"URL: {url}\n"
        msg_content += "-" * 100 + "\n"
        files: List[discord.File] = [await attachment.to_file() for attachment in after.attachments]
        await webhook.send(content=msg_content, files=files,
                           username=after.author.display_name, avatar_url=after.author.display_avatar.url)
        await after.add_reaction("✅")

    @commands.Cog.listener('on_message_delete')
    async def dm_delete_listener(self, message: discord.Message):
        if message.guild or message.author.bot:
            return
        self.bot.logger.info(f"[DELETED DM] from {message.author} ({message.author.id}): {message.content}")
        if not DM_RECIPIENTS_CATEGORY:
            return
        webhook = await self.get_webhook(message.author)
        if not webhook:
            return
        await webhook.send(content=f"- Deleted Message:\n```{message.content}```\n",
                           username=message.author.display_name, avatar_url=message.author.display_avatar.url)

    @commands.Cog.listener('on_message')
    async def send_dm(self, message: discord.Message):
        if message.author.bot:
            return
        assert isinstance(message.channel, discord.TextChannel)
        if message.channel.category_id != DM_RECIPIENTS_CATEGORY:
            return
        if message.author.id != OWNER_ID:
            return
        if message.channel.topic is None:
            return
        reply_msg_id = None
        try:
            user_id = int(message.channel.topic.split(':')[1])
            if message.reference and message.reference.resolved:
                resolved = message.reference.resolved
                assert isinstance(resolved, discord.Message)
                if resolved.content and "MSGID" in resolved.content.splitlines()[0] and resolved.author.bot:
                    reply_msg_id = int(resolved.content.splitlines()[0].split(':')[1])
        except (IndexError, ValueError) as e:
            self.bot.logger.error(f"Failed to parse user ID from channel topic: {message.channel.topic}"
                                  f"\n{e.__class__.__name__}: {e}")
            return
        user = self.bot.get_user(user_id)
        if not user:
            self.bot.logger.error(f"Failed to find user with ID {user_id}")
            return
        try:
            channel = await user.create_dm()
            await channel.send(content=message.content,
                               reference=discord.MessageReference(message_id=reply_msg_id,
                                                                  channel_id=channel.id) if reply_msg_id else None,
                               # type: ignore
                               files=[await attachment.to_file() for attachment in message.attachments],
                               embeds=message.embeds)
            self.bot.logger.info(f"[DM] to {user} ({user.id}): {message.content}")
            await message.add_reaction("✅")
        except discord.Forbidden as e:
            self.bot.logger.error(f"Failed to send DM to {user} ({user.id})\n{e.__class__.__name__}: {e}")
            await message.add_reaction("❌")

    @commands.command(name="dm", hidden=True)
    @commands.is_owner()
    async def dm(self, ctx: commands.Context, user: discord.User, *, msg: str):
        if not msg and not ctx.message.attachments:
            return await ctx.send("Please provide a message to send.")
        files: List[discord.File] = [await attachment.to_file() for attachment in ctx.message.attachments]
        try:
            channel = await user.create_dm()
            message = await channel.send(content=msg, files=files)
            self.bot.logger.info(f"[DM] to {user} ({user.id}): {message.content}")
            await ctx.message.add_reaction("✅")
        except discord.Forbidden as e:
            self.bot.logger.error(f"Failed to send DM to {user} ({user.id})\n{e.__class__.__name__}: {e}")
            await ctx.message.add_reaction("❌")
            return

        # log to DM log channel
        webhook = await self.get_webhook(user)
        if not webhook:
            return
        content = f"MSGID:{message.id}\n\n"
        content += f"- Content:\n```{message.content}```\n"
        # check if content match url pattern regex
        urlmatch = rx_url.match(message.content)
        if urlmatch:
            url = urlmatch.group("url")
            content += f"URL: {url}\n"
        content += "-" * 100 + "\n"
        await webhook.send(content=content, files=files,
                           username=ctx.author.display_name, avatar_url=ctx.author.display_avatar.url)
        await ctx.message.delete()


async def setup(bot: AssistantBot):
    await bot.add_cog(DMRelay(bot))
