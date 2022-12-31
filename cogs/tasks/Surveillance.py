# Imports
from datetime import datetime

import disnake
from disnake import Embed
from disnake.ext import commands

import assistant
from assistant import available_clients, all_activities, colour_gen, getch_hook
from config import owner_id, home_guild, logging_guilds


class Surveillance(commands.Cog):
    def __init__(self, client: assistant.Client):
        self.client = client
        self.logger = client.logger
        self.logging_guilds = logging_guilds

    async def get_webhook(self, _id: int) -> disnake.Webhook | None:
        channel = self.client.get_channel(_id)
        return await getch_hook(channel)

    @commands.Cog.listener()
    async def on_message_edit(self, before: disnake.Message, after: disnake.Message) -> None:
        """
        Logs edited messages
        """
        if before.guild is None:
            return
        if before.author.bot:
            return
        if before.author.id == owner_id:
            return
        if before.clean_content == after.clean_content:
            return
        for name, guild in self.logging_guilds.items():
            if guild["id"] == before.guild.id:
                hook = await self.get_webhook(guild["channel_id"])
                break
        else:
            return
        author = before.author
        embed = Embed(title="Message Edit", description=f"in {before.channel.mention}", colour=colour_gen(author.id))
        embed.add_field(name="Original Message", value=before.clean_content, inline=False)
        embed.add_field(name="Altered Message", value=after.clean_content, inline=False)
        embed.set_footer(text=f"{datetime.now().strftime('%I:%M %p, %d %b')}")
        await hook.send(embed=embed,
                        username=author.display_name, avatar_url=author.display_avatar.url, delete_after=600)
        self.logger.info(f"{author.display_name} edited a message in #{before.channel.name}")

    @commands.Cog.listener()
    async def on_message_delete(self, message: disnake.Message) -> None:
        """
        Logs deleted messages
        """
        if message.guild is None or message.guild.id != home_guild:
            return
        if message.author.bot or message.author.id == owner_id:
            return
        author = message.author
        embed = Embed(title="Deleted Message", description=f"{message.channel.mention}",
                      colour=colour_gen(author.id))
        embed.add_field(name="Message Content", value=message.clean_content, inline=False)
        embed.set_footer(text=f"{datetime.now().strftime('%I:%M %p, %d %b')}")
        hook = await self.get_webhook(self.logging_guilds["homie"]["channel_id"])
        await hook.send(embed=embed,
                        username=author.display_name, avatar_url=author.display_avatar.url, delete_after=600)
        self.logger.info(f"{author.display_name} deleted a message in #{message.channel.name}\n" +
                         f"\tMessage: {message.clean_content}")

    @commands.Cog.listener()
    async def on_member_update(self, before: disnake.Member, after: disnake.Member) -> None:
        """
        Logs when a member updates their Nickname.
        """
        if before.bot:
            return
        if before.id == owner_id:
            return
        if before.display_name == after.display_name:
            return
        embed = Embed(title="Nickname Update", colour=colour_gen(before.id))
        embed.add_field(name="Old Name", value=before.display_name, inline=False)
        embed.add_field(name="New Name", value=after.display_name, inline=False)
        embed.set_footer(text=f"{datetime.now().strftime('%I:%M %p, %d %b')}")
        for name, guild in self.logging_guilds.items():
            if guild["id"] == before.guild.id:
                hook = await self.get_webhook(guild["channel_id"])
                break
        else:
            return
        if hook:
            await hook.send(embed=embed,
                            username=after.display_name, avatar_url=after.display_avatar.url, delete_after=600)
        self.logger.info(f"Nickname update in {before.guild.name}: {before.display_name} -> {after.display_name}")

    @commands.Cog.listener()
    async def on_user_update(self, before: disnake.User, after: disnake.User) -> None:
        """
        Logs when a user updates their username.
        """
        member: disnake.Member = disnake.utils.get(self.client.get_all_members(), id=before.id)
        if member is None:
            return
        if before.bot or before.id == owner_id:
            return
        if str(before) == str(after):
            return
        for name, guild in self.logging_guilds.items():
            if guild["id"] == member.guild.id:
                hook = await self.get_webhook(guild["channel_id"])
                break
        else:
            return
        embed = Embed(colour=colour_gen(before.id))
        embed.set_author(name=f"Username Change", icon_url=before.display_avatar.url)
        embed.add_field(name="Old Username", value=str(before), inline=False, )
        embed.add_field(name="New Username", value=str(after), inline=False, )
        embed.set_footer(text=f"{datetime.now().strftime('%I:%M %p, %d %b')}")
        await hook.send(embed=embed,
                        username=member.display_name, avatar_url=member.display_avatar.url, delete_after=1200)
        self.logger.info(f"Username change in {member.guild.name}: {before} -> {after}")

    @commands.Cog.listener()
    async def on_presence_update(self, before: disnake.Member, after: disnake.Member) -> None:
        """
        Logs when a member changes their status/activity.
        """
        if before.guild is None:
            return
        if before.bot:
            return
        if before.id == owner_id:
            return
        if before.guild.id != home_guild:
            return
        hook = await self.get_webhook(self.logging_guilds["homie"]["channel_id"])
        logger = self.logger
        embed = Embed(title="Presence Update", colour=colour_gen(before.id))
        if available_clients(before) != available_clients(after):
            embed.add_field(name=f"Client/Status", value=f"{available_clients(before)} ──> {available_clients(after)}",
                            inline=False, )
            logger.info(f"[{before.guild.name}] {before}'s client update" +
                        f" {available_clients(before)} -> {available_clients(after)}")
            if before.raw_status == "offline" or after.raw_status == "offline":
                await hook.send(embed=embed,
                                username=after.display_name, avatar_url=after.display_avatar.url, delete_after=1200)
                return

        # Activities
        for b_key, b_value in all_activities(before, with_url=True):
            if b_key == "Spotify":
                continue
            for a_key, a_value in all_activities(after, with_url=True):
                if b_key != a_key or b_value == a_value:
                    continue
                if b_value and not a_value:
                    embed.add_field(name=f"Stopped {b_key}:", value=f"{b_value}", inline=False, )
                    logger.info(f"[{before.guild.name}] {before} stopped {b_key}: {b_value}")
                elif a_value and not b_value:
                    embed.add_field(name=f"Started {b_key}:", value=f"{a_value}", inline=False, )
                    logger.info(f"[{before.guild.name}] {before} started {b_key}: {a_value}")
                else:
                    embed.add_field(name=f"Changed {b_key}:", value=f"{b_value} ──> {a_value}", inline=False, )
                    logger.info(f"[{before.guild.name}] {before} changed {b_key}: {b_value} -> {a_value}")

        if len(embed.fields):
            await hook.send(embed=embed,
                            username=before.display_name, avatar_url=before.display_avatar.url, delete_after=900)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: disnake.Member, before: disnake.VoiceState,
                                    after: disnake.VoiceState) -> None:
        """
        Logs when a member joins/leaves a voice channel.
        """
        if member.bot or member.id == owner_id:
            return
        if after.channel == before.channel or (before is None and after is None):
            return
        if after.channel and not before.channel:
            msg = f"Joined {after.channel.mention}"
            log_msg = f"Joined #{after.channel.name}"
        elif before.channel and not after.channel:
            msg = f"Left {before.channel.mention}"
            log_msg = f"Left #{before.channel.name}"
        else:
            msg = f"Moved from {before.channel.mention} to {after.channel.mention}"
            log_msg = f"Moved from #{before.channel.name} to #{after.channel.name}"

        for name, guild in self.logging_guilds.items():
            if guild["id"] == member.guild.id:
                hook = await self.get_webhook(guild["channel_id"])
                break
        else:
            return
        await hook.send(msg, username=member.display_name, avatar_url=member.display_avatar.url, delete_after=300)
        self.logger.info(f"[{member.guild.name}] {member.display_name}: {log_msg}")

    @commands.Cog.listener()
    async def on_typing(self, channel: disnake.TextChannel, user: disnake.Member, when: datetime) -> None:
        """Logs when a user starts typing in a channel."""
        if isinstance(channel, disnake.DMChannel):
            return
        if channel.guild.id != home_guild:
            return
        if user.bot or user.id == owner_id:
            return
        hook = await self.get_webhook(self.logging_guilds["homie"]["channel_id"])
        await hook.send(f"Started typing in {channel.mention}",
                        username=user.display_name, avatar_url=user.display_avatar.url, delete_after=120)
        self.logger.info(f"{user.display_name} started typing in {channel.name} on {when}")

    @commands.Cog.listener()
    async def on_raw_member_remove(self, payload: disnake.RawGuildMemberRemoveEvent) -> None:
        """Logs when a member leaves a server."""
        if payload.user.bot:
            return
        if payload.guild_id == home_guild:
            hook = await self.get_webhook(self.logging_guilds["homie"]["channel_id"])
            await hook.send(f"{payload.user.display_name} left the server.",
                            username=payload.user.display_name,
                            avatar_url=payload.user.display_avatar.url)
        self.logger.info(f"{payload.user} left {self.client.get_guild(payload.guild_id).name}")

    @commands.Cog.listener()
    async def on_member_join(self, member: disnake.Member) -> None:
        """Logs when a member joins a server."""
        if member.bot:
            return
        if member.guild.id == home_guild:
            hook = await self.get_webhook(self.logging_guilds["homie"]["channel_id"])
            await hook.send(f"{member.display_name} joined the server",
                            username=member.display_name, avatar_url=member.display_avatar.url)
        self.logger.info(f"{member.display_name} joined {member.guild.name}")

    @commands.Cog.listener()
    async def on_member_ban(self, guild: disnake.Guild, user: disnake.User) -> None:
        """Logs when a member is banned from a server."""
        if user.bot:
            return
        if guild.id == home_guild:
            hook = await self.get_webhook(self.logging_guilds["homie"]["channel_id"])
            await hook.send(f"{user.display_name} was banned from the server",
                            username=user.display_name, avatar_url=user.display_avatar.url)
        self.logger.info(f"{user.display_name} was banned from {guild.name}")

    @commands.Cog.listener()
    async def on_member_unban(self, guild: disnake.Guild, user: disnake.User) -> None:
        """Logs when a member is unbanned from a server."""
        if user.bot:
            return
        if guild.id == home_guild:
            hook = await self.get_webhook(self.logging_guilds["homie"]["channel_id"])
            await hook.send(f"{user.display_name} was unbanned from the server",
                            username=user.display_name, avatar_url=user.display_avatar.url)
        self.logger.info(f"{user.display_name} was unbanned from {guild.name}")


def setup(client):
    if all([home_guild, logging_guilds, owner_id]):
        client.add_cog(Surveillance(client))
    else:
        client.logger.warning("Logging is disabled due to missing config values.")
