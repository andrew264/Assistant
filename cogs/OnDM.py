﻿# Imports
import disnake
from disnake.ext import commands

from EnvVariables import DM_Channel


class OnDM(commands.Cog):
    def __init__(self, client: disnake.Client):
        self.client = client

    # Replies
    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message) -> None:
        if message.guild:
            return
        if message.author.bot:
            return
        else:
            channel = self.client.get_channel(DM_Channel)
            msg_content = "──────────────────────────────\n"
            msg_content += f"UserID: `{message.author.id}`\nMessage Author: `{message.author}`"
            if len(message.content):
                msg_content += f"\n Message:\n```{message.content}```"
            if len(message.attachments):
                msg_content += "\nAttachments: "
                for attachment in message.attachments:
                    msg_content += f"\n{str(attachment)}"
            msg_content += "\n──────────────────────────────"
            if isinstance(channel, disnake.TextChannel):
                await channel.send(msg_content)

    # slide to dms
    @commands.command()
    @commands.is_owner()
    async def dm(self, ctx: commands.Context, user: disnake.User, *, msg: str) -> None:
        channel = await user.create_dm()
        msg_content = f"{msg}\n"
        if ctx.message.attachments:
            for attachment in ctx.message.attachments:
                msg_content += f"{str(attachment)}\n"
        try:
            await channel.send(msg_content)
        except (disnake.Forbidden | disnake.HTTPException):
            await ctx.send(f"Failed to DM {user}.")


def setup(client):
    client.add_cog(OnDM(client))
