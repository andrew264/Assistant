# Imports
from typing import List

import disnake
from disnake.ext import commands

from EnvVariables import DM_Channel
from assistant import Client, getch_hook


class OnDM(commands.Cog):
    def __init__(self, client: Client):
        self.client = client
        self.logger = client.logger

    # Replies
    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message) -> None:
        if message.guild or message.author.bot:
            return
        msg_content = f"UserID: `{message.author.id}`\n"
        if message.content:
            msg_content += f"Content: ```{message.content}```\n"
        files: List[disnake.File] = [await attachment.to_file() for attachment in message.attachments]
        webhook = await getch_hook(self.client.get_channel(DM_Channel))
        await webhook.send(content=msg_content, files=files,
                           username=str(message.author), avatar_url=message.author.display_avatar.url)
        self.logger.info(f"Received a message from {message.author}")

    # slide to dms
    @commands.command()
    @commands.is_owner()
    async def dm(self, ctx: commands.Context, user: disnake.User, *, msg: str = "") -> None:
        files: List[disnake.File] = [await attachment.to_file() for attachment in ctx.message.attachments]
        if not msg and not files:
            await ctx.send("Please provide a message or an attachment")
            return
        try:
            await user.send(content=msg if msg else None, files=files)
        except (disnake.Forbidden | disnake.HTTPException):
            await ctx.send(f"Failed to DM {user}.")
            self.logger.warning(f"Failed to DM {user}.")
        else:
            await ctx.send(f"DM'd {user}.")
            self.logger.info(f"DM'd {user}.")

        # log Sent Direct Messages
        dm = self.client.get_channel(DM_Channel)
        await dm.send(content=f"From: **{ctx.author}**\nTo: **{user}**.\nContent: *{msg}*", files=files, )
        await ctx.message.delete()


def setup(client):
    client.add_cog(OnDM(client))
