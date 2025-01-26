import json
import os
import random
from typing import List, Optional

import discord
from discord import app_commands
from discord.ext import commands

from assistant import AssistantBot
from config import OWNER_ID, RESOURCE_PATH


class Funny(commands.Cog):
    def __init__(self, bot: AssistantBot, death_msgs: List[str]):
        self.bot = bot
        self._death_msgs_template = death_msgs

    def _get_death_msg(self, user1: discord.Member, user2: discord.Member) -> str:
        if random.random() < 0.1:
            user1, user2 = user2, user1
        msg = random.choice(self._death_msgs_template)
        return msg.format(user1=user1.mention, user2=user2.mention, user3=self.bot.user.mention)

    @commands.hybrid_command(name='kill', description='Delete their existence')
    @app_commands.describe(user='Who should I kill?')
    @commands.guild_only()
    async def kill(self, ctx: commands.Context, user: discord.Member):
        if user == ctx.author:
            await ctx.send(content="Stop, Get some Help.")
            return
        embed = discord.Embed(colour=discord.Colour.red())
        embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
        if user.bot:
            embed.description = "You cannot attack my kind."
        else:
            embed.description = self._get_death_msg(user, ctx.author)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='pp', description='Check your pp size')
    @commands.guild_only()
    @app_commands.describe(user='Whose pp should I check?')
    async def pp(self, ctx: commands.Context, user: Optional[discord.Member] = None):
        if user is None:
            user = ctx.author

        embed = discord.Embed(colour=discord.Colour.red())
        embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
        special_characters = [OWNER_ID, ]
        if user.id in special_characters:
            embed.description = f'[8{"=" * random.randint(7, 12)}D]' + '(https://www.youtube.com/watch?v=dQw4w9WgXcQ "Ran out of Tape while measuring")'
        elif user.bot:
            embed.description = f'404 Not Found'
        else:
            embed.description = f"8{'=' * random.randint(0, 9)}D"
        await ctx.send(embed=embed)

    @app_commands.command(name='flames', description='Check your relationship with someone')
    @commands.guild_only()
    @app_commands.describe(user1='Who is the first person?', user2='Who is the second person?')
    @app_commands.rename(user1='first-person', user2='second-person')
    async def flames(self, ctx: discord.Interaction, user1: str, user2: Optional[str] = None):
        if user2 is None:
            user2 = ctx.user.display_name
        flames = ['Friends', 'Lovers', 'Angry', 'Married', 'Enemies', 'Soulmates']
        o_name1, o_name2 = user1, user2
        user1, user2 = user1.lower(), user2.lower()
        user1.replace(' ', '')
        user2.replace(' ', '')

        if user1 == user2:
            await ctx.response.send_message(content="Stop, Get some Help.")
            return

        for char in user1:
            if char in user2:
                user1 = user1.replace(char, '', 1)
                user2 = user2.replace(char, '', 1)

        count = len(user1) + len(user2)
        flames = flames[count % len(flames)]
        embed = discord.Embed(colour=discord.Colour.red(), title=f'{o_name1} and {o_name2}')
        embed.description = f'are {flames}'
        await ctx.response.send_message(embed=embed)


async def setup(bot: AssistantBot):
    msgs: List[str] = ['{user1} was killed by {user2}']
    death_msg_file = 'death-messages.json'
    death_msg_path = os.path.join(RESOURCE_PATH, death_msg_file)
    if os.path.isfile(death_msg_path):
        bot.logger.info(f'[LOADED] death messages from {death_msg_file}')
        with open(death_msg_path, 'r') as f:
            death_msgs: dict = json.load(f)
            msgs = death_msgs['messages']
    await bot.add_cog(Funny(bot, msgs))
