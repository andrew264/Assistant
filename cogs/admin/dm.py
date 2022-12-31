# Imports
import re
from typing import List, Optional

import disnake
from disnake.ext import commands

from assistant import Client, getch_hook
from config import dm_receive_category, owner_id, home_guild

rx_url = re.compile(r"(?P<url>https?://[^\s]+)")


class OnDM(commands.Cog):
    def __init__(self, client: Client):
        self.client = client
        self.logger = client.logger

    async def get_webhook(self, user: disnake.User) -> Optional[disnake.Webhook]:
        guild = self.client.get_guild(home_guild)
        if guild is None:
            return None
        category = guild.get_channel(dm_receive_category)
        if category is None:
            return None
        for channel in category.channels:
            if channel.topic and str(user.id) in channel.topic:
                webhook = await getch_hook(channel)
                break
        else:
            channel = await category.create_text_channel(
                name=f"{user.name}-{user.discriminator}",
                topic=f"UserID: {user.id}")
            webhook = await getch_hook(channel)
        return webhook

    # Receive DMs
    @commands.Cog.listener('on_message')
    async def receive_messages(self, message: disnake.Message) -> None:
        if message.guild or message.author.bot:
            return
        self.client.logger.info(f"{message.author}: {message.content}")
        if not dm_receive_category:
            return
        hook = await self.get_webhook(message.author)
        if hook is None:
            return

        msg_content = f"Message ID: `{message.id}`"
        if message.reference:
            msg_content += f"; Replying to: `{message.reference.resolved.content[:100]}`"
        if message.content:
            msg_content += f"\nContent: ```{message.content}```\n"
        # check if content match url pattern regex
        if message.content and rx_url.match(message.content):
            url = rx_url.match(message.content).group("url")
            msg_content += f"URL: {url}\n"
        files: List[disnake.File] = [await attachment.to_file() for attachment in message.attachments]
        await hook.send(content=msg_content, files=files,
                        username=message.author.name, avatar_url=message.author.display_avatar.url)

    # Send DMs
    @commands.Cog.listener('on_message')
    async def send_message(self, message: disnake.Message) -> None:
        if message.author.bot:
            return
        if message.author.id != owner_id and not message.guild:
            return
        if isinstance(message.channel, disnake.DMChannel):
            return
        if not message.channel.category_id == dm_receive_category:
            return
        if message.channel.topic is None:
            return
        reply_msg_id = None
        try:
            user_id = int(message.channel.topic.split("UserID: ")[1])
            if message.reference and message.reference.resolved:
                resolved = message.reference.resolved
                if resolved.content and "Message ID: " in resolved.content and resolved.author.bot:
                    reply_msg_id = int(resolved.content
                                       .split("\n", 1)[0]
                                       .split("Message ID: ")[1]
                                       .split(";")[0]
                                       .replace("`", ""))
        except (IndexError, ValueError):
            self.logger.error(
                f"Invalid 'user_id' or 'reply_msg_id' in `{message.channel.topic}` or `{message.content}`")
            return
        user = self.client.get_user(user_id)
        if not user:
            return
        try:
            channel = await user.create_dm()
            await user.send(content=message.content,
                            reference=disnake.MessageReference(message_id=reply_msg_id,
                                                               channel_id=channel.id) if reply_msg_id else None,
                            files=[await attachment.to_file() for attachment in message.attachments],
                            embeds=[embed for embed in message.embeds])
            self.logger.info(f"Sent a message to {user}")
        except (disnake.Forbidden, disnake.HTTPException):
            await message.channel.send(f"Failed to DM {user}.")
            self.logger.warning(f"Failed to DM {user}.")

    # Send DMs but with a command
    @commands.command()
    @commands.is_owner()
    async def dm(self, ctx: commands.Context, user: disnake.User, *, msg: str = "") -> None:
        if not msg and not ctx.message.attachments:
            await ctx.send("Please provide a message or an attachment")
            return
        files: List[disnake.File] = [await attachment.to_file() for attachment in ctx.message.attachments]
        try:
            msg = await user.send(content=msg if msg else None, files=files)
        except (disnake.Forbidden, disnake.HTTPException):
            await ctx.send(f"Failed to DM {user}.")
            self.logger.warning(f"Failed to DM {user}.")
        else:
            await ctx.send(f"DM'd {user}.")
            self.logger.info(f"DM'd {user}.")

        # log Sent Direct Messages
        hook = await self.get_webhook(user)
        content = f"Message ID: `{msg.id}`\n"
        content += f"\nContent: ```{msg.content}```\n"
        # check if content match url pattern regex
        if msg and rx_url.match(msg):
            url = rx_url.match(msg).group("url")
            content += f"URL: {url}\n"
        await hook.send(content=content, files=files,
                        username=ctx.author.name, avatar_url=ctx.author.display_avatar.url)
        await ctx.message.delete()


def setup(client):
    if all([dm_receive_category, owner_id, home_guild]):
        client.add_cog(OnDM(client))
    else:
        client.logger.warning("DMs cog is disabled due to missing config values.")
