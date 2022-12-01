# Imports
from typing import List, Optional

import disnake
from disnake.ext import commands

from EnvVariables import DM_Channel, Owner_ID
from assistant import Client, getch_hook


class OnDM(commands.Cog):
    def __init__(self, client: Client):
        self.client = client
        self.logger = client.logger

    # Replies
    @commands.Cog.listener('on_message')
    async def receive_messages(self, message: disnake.Message) -> None:
        if message.guild or message.author.bot:
            return
        msg_content = f"UserID: `{message.author.id}`; Message ID: `{message.id}`"
        if message.reference:
            msg_content += f"; Replying to: `{message.reference.message_id}`"
        if message.content:
            msg_content += f"\nContent: ```{message.content}```\n"
        files: List[disnake.File] = [await attachment.to_file() for attachment in message.attachments]
        webhook = await getch_hook(self.client.get_channel(DM_Channel))
        await webhook.send(content=msg_content, files=files,
                           username=str(message.author), avatar_url=message.author.display_avatar.url)
        self.logger.info(f"Received a message from {message.author}")

    @commands.Cog.listener('on_message')
    async def send_message(self, message: disnake.Message) -> None:
        if message.author.id != Owner_ID and not message.guild:
            return
        if not message.reference:
            return
        if message.reference.resolved.author.id != self.client.user.id and not message.reference.resolved.webhook_id:
            return
        if not message.reference.resolved.content.startswith("UserID:"):
            return
        try:
            msg = message.reference.resolved.content.splitlines()[0].split(';')
            user_id: int = int(msg[0].split(':')[1].replace("`", ""))
            msg_id: Optional[int] = int(msg[1].split(':')[1].replace("`", "")) if len(msg) > 1 else None
        except (IndexError, ValueError):
            self.logger.warning(f"Invalid message reference: {message.reference.resolved.content}")
            return
        content = message.content
        user = self.client.get_user(user_id)
        if not user:
            return
        try:
            channel = await user.create_dm()
            await user.send(content=content,
                            reference=disnake.MessageReference(message_id=msg_id,
                                                               channel_id=channel.id) if msg_id else None,
                            files=[await attachment.to_file() for attachment in message.attachments],
                            embeds=[embed for embed in message.embeds])
            self.logger.info(f"Sent a message to {user}")
        except (disnake.Forbidden, disnake.HTTPException):
            await message.channel.send(f"Failed to DM {user}.")
            self.logger.warning(f"Failed to DM {user}.")

    # slide to dms
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
        dm_log = self.client.get_channel(DM_Channel)
        content = f"UserID: `{user.id}`; Message ID: `{msg.id}`\n"
        content += f"To: `{user}`; From: `{ctx.author}`\n"
        content += f"\nContent: ```{msg.content}```\n"
        await dm_log.send(content=content, files=files, )
        await ctx.message.delete()


def setup(client):
    client.add_cog(OnDM(client))
