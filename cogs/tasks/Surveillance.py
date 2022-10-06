# Imports
from datetime import datetime

import disnake
from disnake import Embed
from disnake.ext import commands

import assistant
from EnvVariables import *
from assistant import available_clients, all_activities, colour_gen, getch_hook


class Surveillance(commands.Cog):
    def __init__(self, client: assistant.Client):
        self.client = client
        self.logger = client.logger

    @property
    def homies_log(self):
        return self.client.get_channel(HOMIES_LOG)

    @property
    def prob_log(self):
        return self.client.get_channel(PROB_LOG)

    @commands.Cog.listener()
    async def on_message_edit(self, before: disnake.Message, after: disnake.Message) -> None:
        if before.guild is None or before.guild.id != HOMIES:
            return
        if before.author.bot:
            return
        if before.author.id == Owner_ID:
            return
        if before.clean_content == after.clean_content:
            return
        author = before.author
        embed = Embed(title="Message Edit", description=f"in {before.channel.mention}", colour=colour_gen(author.id))
        embed.add_field(name="Original Message", value=before.clean_content, inline=False)
        embed.add_field(name="Altered Message", value=after.clean_content, inline=False)
        embed.set_footer(text=f"{datetime.now().strftime('%I:%M %p, %d %b')}")
        hook = await getch_hook(self.homies_log)
        await hook.send(embed=embed,
                        username=author.display_name, avatar_url=author.display_avatar.url, delete_after=600)
        self.logger.info(f"{author.display_name} edited a message in #{before.channel.name}")

    @commands.Cog.listener()
    async def on_message_delete(self, message: disnake.Message) -> None:
        if message.guild is None or message.guild.id != HOMIES:
            return
        if message.author.bot or message.author.id == Owner_ID:
            return
        author = message.author
        embed = Embed(title="Deleted Message", description=f"{message.channel.mention}",
                      colour=colour_gen(author.id))
        embed.add_field(name="Message Content", value=message.clean_content, inline=False)
        embed.set_footer(text=f"{datetime.now().strftime('%I:%M %p, %d %b')}")
        hook = await getch_hook(self.homies_log)
        await hook.send(embed=embed,
                        username=author.display_name, avatar_url=author.display_avatar.url, delete_after=600)
        self.logger.info(f"{author.display_name} deleted a message in #{message.channel.name}")

    @commands.Cog.listener()
    async def on_member_update(self, before: disnake.Member, after: disnake.Member) -> None:
        if before.guild.id not in (HOMIES, PROB):
            return
        if before.bot:
            return
        if before.id == Owner_ID:
            return
        if before.display_name == after.display_name:
            return
        embed = Embed(title="Nickname Update", colour=colour_gen(before.id))
        embed.add_field(name="Old Name", value=before.display_name, inline=False)
        embed.add_field(name="New Name", value=after.display_name, inline=False)
        embed.set_footer(text=f"{datetime.now().strftime('%I:%M %p, %d %b')}")
        hook = None
        if before.guild.id == PROB:
            hook = await getch_hook(self.prob_log)
        elif before.guild.id == HOMIES:
            hook = await getch_hook(self.homies_log)
        if hook:
            await hook.send(embed=embed,
                            username=after.display_name, avatar_url=after.display_avatar.url, delete_after=600)
        self.logger.info(f"Nickname update: {before.display_name} -> {after.display_name}")

    @commands.Cog.listener()
    async def on_user_update(self, before: disnake.User, after: disnake.User) -> None:
        member = self.client.get_guild(HOMIES).get_member(before.id)
        if member is None:
            return
        if before.bot or before.id == Owner_ID:
            return
        if str(before) == str(after):
            return
        embed = Embed(colour=colour_gen(before.id))
        embed.set_author(name=f"Username Change", icon_url=before.display_avatar.url)
        embed.add_field(name="Old Username", value=str(before), inline=False, )
        embed.add_field(name="New Username", value=str(after), inline=False, )
        embed.set_footer(text=f"{datetime.now().strftime('%I:%M %p, %d %b')}")
        hook = await getch_hook(self.homies_log)
        await hook.send(embed=embed,
                        username=member.display_name, avatar_url=member.display_avatar.url, delete_after=1200)
        self.logger.info(f"Username change: {before} -> {after}")

    @commands.Cog.listener()
    async def on_presence_update(self, before: disnake.Member, after: disnake.Member) -> None:
        if before.guild is None or before.guild.id != HOMIES:
            return
        if before.bot:
            return
        if before.id == Owner_ID:
            return
        hook = await getch_hook(self.homies_log)
        logger = self.logger
        embed = Embed(title="Presence Update", colour=colour_gen(before.id))
        if available_clients(before) != available_clients(after):
            embed.add_field(name=f"Client/Status", value=f"{available_clients(before)} ──> {available_clients(after)}",
                            inline=False, )
            logger.info(f"{before}'s client update {available_clients(before)} -> {available_clients(after)}")
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
                    logger.info(f"{before} stopped {b_key}: {b_value}")
                elif a_value and not b_value:
                    embed.add_field(name=f"Started {b_key}:", value=f"{a_value}", inline=False, )
                    logger.info(f"{before} started {b_key}: {a_value}")
                else:
                    embed.add_field(name=f"Changed {b_key}:", value=f"{b_value} ──> {a_value}", inline=False, )
                    logger.info(f"{before} changed {b_key}: {b_value} -> {a_value}")

        if len(embed.fields):
            await hook.send(embed=embed,
                            username=before.display_name, avatar_url=before.display_avatar.url, delete_after=900)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: disnake.Member, before: disnake.VoiceState,
                                    after: disnake.VoiceState) -> None:
        if member.guild.id not in (HOMIES, PROB):
            return
        if member.bot or member.id == Owner_ID:
            return
        if after.channel == before.channel or (before is None and after is None):
            return
        if after.channel and not before.channel:
            msg = f"Joined {after.channel.mention}"
            log_msg = f"Joined {after.channel.name}"
        elif before.channel and not after.channel:
            msg = f"Left {before.channel.mention}"
            log_msg = f"Left {before.channel.name}"
        else:
            msg = f"Moved from {before.channel.mention} to {after.channel.mention}"
            log_msg = f"Moved from {before.channel.name} to {after.channel.name}"
        hook = None
        if member.guild.id == PROB:
            hook = await getch_hook(self.prob_log)
        elif member.guild.id == HOMIES:
            hook = await getch_hook(self.homies_log)
        if hook:
            await hook.send(msg, username=member.display_name, avatar_url=member.display_avatar.url, delete_after=300)
        self.logger.info(f"{member.display_name}: {log_msg}")

    @commands.Cog.listener()
    async def on_typing(self, channel: disnake.TextChannel, user: disnake.Member, when: datetime) -> None:
        if isinstance(channel, disnake.DMChannel):
            return
        if channel.guild.id != HOMIES:
            return
        if user.bot or user.id == Owner_ID:
            return
        await self.homies_log.send(f"{user.display_name} started typing in {channel.mention}", delete_after=120)
        self.logger.info(f"{user.display_name} started typing in {channel.name}")


def setup(client):
    client.add_cog(Surveillance(client))
