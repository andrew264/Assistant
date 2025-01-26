# Imports
from datetime import datetime
from typing import Optional

import discord
from discord import Embed, Status
from discord.ext import commands

from assistant import AssistantBot
from config import HOME_GUILD_ID, LOGGING_GUILDS, OWNER_ID
from utils import all_activities


class Surveillance(commands.Cog):
    def __init__(self, bot: AssistantBot):
        self.bot = bot
        self.logger = bot.logger.getChild("surveillance")

    async def get_webhook(self, _id: int) -> Optional[discord.Webhook]:
        try:
            channel = self.bot.get_channel(_id)
            assert isinstance(channel, (discord.TextChannel, discord.Thread))
            webhooks = await channel.webhooks()
            for w in webhooks:
                if w.name == "Assistant":
                    return w
            else:
                return await channel.create_webhook(name="Assistant", avatar=await self.bot.user.display_avatar.read())
        except discord.Forbidden as e:
            self.logger.error(f"Failed to get webhook: {e}")
            return None

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        """
        Logs edited messages
        """
        if before.guild is None:
            return
        if before.author.bot:
            return
        if before.author.id == OWNER_ID:
            return
        if before.clean_content == after.clean_content:
            return
        for name, guild in LOGGING_GUILDS.items():
            if guild["guild_id"] == before.guild.id:
                hook = await self.get_webhook(guild["channel_id"])
                break
        else:
            return
        author = before.author
        embed = Embed(title="Message Edit", description=f"in {before.channel.mention}", colour=discord.Colour.red())
        embed.add_field(name="Original Message", value=before.clean_content, inline=False)
        embed.add_field(name="Altered Message", value=after.clean_content, inline=False)
        embed.set_footer(text=f"{datetime.now().strftime('%I:%M %p, %d %b')}")
        if hook:
            await hook.send(embed=embed, username=author.display_name, avatar_url=author.display_avatar.url)
        self.logger.info(f"[MESSAGE EDIT] @{author.display_name} in #{before.channel.name}")

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        """
        Logs deleted messages
        """
        if message.guild is None or message.guild.id != HOME_GUILD_ID:
            return
        if message.author.bot or message.author.id == OWNER_ID:
            return
        author = message.author
        embed = Embed(title="Deleted Message", description=f"{message.channel.mention}", colour=discord.Colour.red())
        embed.add_field(name="Message Content", value=message.clean_content, inline=False)
        if message.attachments:
            embed.add_field(name="Attachments", value="\n".join([attachment.url for attachment in message.attachments]), inline=False)
        embed.set_footer(text=f"{datetime.now().strftime('%I:%M %p, %d %b')}")
        hook = await self.get_webhook(LOGGING_GUILDS["homie"]["channel_id"])
        if hook:
            await hook.send(embed=embed, username=author.display_name, avatar_url=author.display_avatar.url)
        self.logger.info(f"[MESSAGE DELETE] @{author.display_name} in #{message.channel.name}\n" + f"\tMessage: {message.clean_content}")

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        """
        Logs when a member updates their Nickname.
        """
        if before.bot:
            return
        if before.id == OWNER_ID:
            return
        if before.display_name == after.display_name:
            return
        embed = Embed(title="Nickname Update", colour=discord.Colour.red())
        embed.add_field(name="Old Name", value=before.display_name, inline=False)
        embed.add_field(name="New Name", value=after.display_name, inline=False)
        embed.set_footer(text=f"{datetime.now().strftime('%I:%M %p, %d %b')}")
        for name, guild in LOGGING_GUILDS.items():
            if guild["guild_id"] == before.guild.id:
                hook = await self.get_webhook(guild["channel_id"])
                break
        else:
            return
        if hook:
            await hook.send(embed=embed, username=after.display_name, avatar_url=after.display_avatar.url)
        self.logger.info(f"[UPDATE] Nickname {before.guild.name}: @{before.display_name} -> @{after.display_name}")

    @commands.Cog.listener()
    async def on_user_update(self, before: discord.User, after: discord.User) -> None:
        """
        Logs when a user updates their username.
        """
        member: discord.Member = discord.utils.get(self.bot.get_all_members(), id=before.id)
        if member is None:
            return
        if before.bot or before.id == OWNER_ID:
            return
        if str(before) == str(after):
            return
        for name, guild in LOGGING_GUILDS.items():
            if guild["guild_id"] == member.guild.id:
                hook = await self.get_webhook(guild["channel_id"])
                break
        else:
            return
        embed = Embed(colour=discord.Colour.red())
        embed.set_author(name=f"Username Change", icon_url=before.display_avatar.url)
        embed.add_field(name="Old Username", value=str(before), inline=False, )
        embed.add_field(name="New Username", value=str(after), inline=False, )
        embed.set_footer(text=f"{datetime.now().strftime('%I:%M %p, %d %b')}")
        if hook:
            await hook.send(embed=embed, username=member.display_name, avatar_url=member.display_avatar.url)
        self.logger.info(f"[UPDATE] Username {member.guild.name}: @{before} -> @{after}")

    @commands.Cog.listener()
    async def on_presence_update(self, before: discord.Member, after: discord.Member) -> None:
        """
        Logs when a member changes their status/activity.
        """
        if before.bot:
            return
        if before.guild is None or before.guild.id != HOME_GUILD_ID:
            return
        if before.id == OWNER_ID:
            return
        hook = await self.get_webhook(LOGGING_GUILDS["homie"]["channel_id"])
        logger = self.logger
        msg_parts = []

        def get_clients(m: discord.Member) -> list[str]:
            c = []
            if m.desktop_status != Status.offline: c.append("Desktop")
            if m.mobile_status != Status.offline: c.append("Mobile")
            if m.web_status != Status.offline: c.append("Web")
            return c

        b_clients, a_clients = get_clients(before), get_clients(after)
        if b_clients != a_clients:
            clients_str = f"{', '.join(b_clients)} -> {', '.join(a_clients)}"
            msg_parts.append(clients_str)
            logger.info(f"[UPDATE] Client device for @{before} in {before.guild.name} | {clients_str}")

        b_status, a_status = before.raw_status, after.raw_status
        if b_status != a_status:
            status_str = f"{b_status} -> {a_status}"
            msg_parts.append(status_str)
            logger.info(f"[UPDATE] Client status for @{before} in {before.guild.name} | {status_str}")

        if "offline" in (b_status, a_status):
            msg = "\n".join(msg_parts)
            if hook:
                await hook.send(msg, username=after.display_name, avatar_url=after.display_avatar.url)

        # Activities
        b_activities = all_activities(before, with_url=True)
        a_activities = all_activities(after, with_url=True)
        all_keys = set(b_activities.keys()).union(a_activities.keys())
        for key in all_keys:
            if key == "Spotify":
                continue
            b_value = b_activities.get(key)
            a_value = a_activities.get(key)
            if b_value == a_value:
                continue
            change = ""
            if key == 'Custom Status':
                if b_value != a_value:
                    change = f"Custom Status: {b_value} -> {a_value}"
            elif not b_value:
                change = f"Started {key}: {a_value}"
            elif not a_value:
                change = f"Stopped {key}: {b_value}"
            else:
                change = f"{key}: {b_value} -> {a_value}"
            if change:
                msg_parts.append(change)
                logger.info(f"[UPDATE] Presence {before.guild.name}: @{before} {change}")

        msg = "\n".join(msg_parts).strip()
        if msg and hook:
            await hook.send(msg, username=before.display_name, avatar_url=before.display_avatar.url)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState) -> None:
        """
        Logs when a member joins/leaves a voice channel.
        """
        if member.bot or member.id == OWNER_ID:
            return
        if after.channel == before.channel or (before is None and after is None):
            return
        if after.channel and not before.channel:
            msg = f"🏞️ -> {after.channel.mention}"
            log_msg = f"🏞️ -> #{after.channel.name}"
        elif before.channel and not after.channel:
            msg = f"{before.channel.mention} -> 🏞️"
            log_msg = f"#{before.channel.name} -> 🏞️"
        else:
            msg = f"{before.channel.mention} -> {after.channel.mention}"
            log_msg = f"#{before.channel.name} -> #{after.channel.name}"

        for name, guild in LOGGING_GUILDS.items():
            if guild["guild_id"] == member.guild.id:
                hook = await self.get_webhook(guild["channel_id"])
                break
        else:
            return
        if hook:
            await hook.send(msg, username=member.display_name, avatar_url=member.display_avatar.url)
        self.logger.info(f"[UPDATE] Voice {member.guild.name}: @{member.display_name}: {log_msg}")

    @commands.Cog.listener()
    async def on_typing(self, channel: discord.TextChannel, user: discord.Member, when: datetime) -> None:
        """Logs when a user starts typing in a channel."""
        if isinstance(channel, discord.DMChannel):
            return
        if channel.guild.id != HOME_GUILD_ID:
            return
        if user.bot or user.id == OWNER_ID:
            return
        # hook = await self.get_webhook(LOGGING_GUILDS["homie"]["channel_id"])
        # await hook.send(f"Started typing in {channel.mention}",
        #                 username=user.display_name, avatar_url=user.display_avatar.url)
        self.logger.info(f"[UPDATE] Typing @{user.display_name} - #{channel.name} on "
                         f"{when.now().strftime('%d/%m/%Y at %I:%M:%S %p')}")

    @commands.Cog.listener()
    async def on_raw_member_remove(self, payload: discord.RawMemberRemoveEvent) -> None:
        """Logs when a member leaves a server."""
        if payload.user.bot:
            return
        if payload.guild_id == HOME_GUILD_ID:
            hook = await self.get_webhook(LOGGING_GUILDS["homie"]["channel_id"])
            if hook:
                await hook.send(f"{payload.user.display_name} left the server.", username=payload.user.display_name, avatar_url=payload.user.display_avatar.url)
        self.logger.info(f"[GUILD] Leave @{payload.user.name}: {self.bot.get_guild(payload.guild_id).name}")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """Logs when a member joins a server."""
        if member.bot:
            return
        if member.guild.id == HOME_GUILD_ID:
            hook = await self.get_webhook(LOGGING_GUILDS["homie"]["channel_id"])
            if hook:
                await hook.send(f"{member.display_name} joined the server", username=member.display_name, avatar_url=member.display_avatar.url)
        self.logger.info(f"[GUILD] Join @{member.name}: {member.guild.name}")

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User) -> None:
        """Logs when a member is banned from a server."""
        if user.bot:
            return
        if guild.id == HOME_GUILD_ID:
            hook = await self.get_webhook(LOGGING_GUILDS["homie"]["channel_id"])
            if hook:
                await hook.send(f"{user.display_name} was banned from the server", username=user.display_name, avatar_url=user.display_avatar.url)
        self.logger.info(f"[GUILD] Ban @{user.name}: {guild.name}")

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User) -> None:
        """Logs when a member is unbanned from a server."""
        if user.bot:
            return
        if guild.id == HOME_GUILD_ID:
            hook = await self.get_webhook(LOGGING_GUILDS["homie"]["channel_id"])
            if hook:
                await hook.send(f"{user.display_name} was unbanned from the server", username=user.display_name, avatar_url=user.display_avatar.url)
        self.logger.info(f"[GUILD] Unban @{user.name}: {guild.name}")


async def setup(bot: AssistantBot):
    if all([HOME_GUILD_ID, LOGGING_GUILDS, OWNER_ID]):
        await bot.add_cog(Surveillance(bot))
    else:
        bot.logger.warning("[FAILED] Surveillance cog not loaded. Missing config values.")
