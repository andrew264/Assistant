import random
from typing import Optional

import asyncpraw as praw
import discord
from asyncpraw.models import Submission
from discord import app_commands
from discord.ext import commands

from assistant import AssistantBot
from config import RedditConfig

gif_sites = ("redgifs.com", "v.redd.it", "imgur.com")


class RedditCommands(commands.Cog):
    def __init__(self, bot: AssistantBot, reddit: praw.Reddit):
        self.bot = bot
        self._r_cache: dict[str, list[Submission]] = {}
        self.reddit = reddit

    async def get_random_posts(self, subreddit: str, uploaded: str, limit: Optional[int] = 1, over_18: bool = False) -> list[Submission]:
        subreddit = await self.reddit.subreddit(subreddit)
        if subreddit.display_name not in self._r_cache:
            self._r_cache[subreddit.display_name] = []
            try:
                async for submission in subreddit.top(uploaded, limit=100):
                    self._r_cache[subreddit.display_name].append(submission)
            except Exception as e:
                self.bot.logger.error(f"Error while fetching posts from {subreddit.display_name}: {e}")
                return []
        if over_18 is False:
            return random.sample([x for x in self._r_cache[subreddit.display_name] if x.over_18 is False], limit)
        else:
            return random.sample(self._r_cache[subreddit.display_name], limit)

    @staticmethod
    def process_link(url: str):
        if url.endswith(".gifv"):
            return url[:-1]
        else:
            return url

    class CustomUrl(discord.ui.View):
        def __init__(self, url: str, label: str):
            super().__init__()
            self.add_item(discord.ui.Button(style=discord.ButtonStyle.link, label=label, url=url))

    @commands.hybrid_command(name='meme', description='Get a random meme from a subreddit')
    async def meme(self, ctx: commands.Context) -> None:
        await ctx.defer()
        sub_list = ("memes", "dankmemes", "funny")
        subreddit = random.choice(sub_list)
        post = (await self.get_random_posts(subreddit, "day"))[0]
        embed = discord.Embed(title=post.title, colour=0xFF5700)
        embed.set_author(name=f"Uploaded by u/{post.author.name} on {post.subreddit_name_prefixed}", url=f"https://reddit.com{post.permalink}")
        embed.set_footer(text=f"Requested by: {ctx.author.display_name}")
        if any(vid in post.url for vid in gif_sites):
            await ctx.send(content="", embed=embed)
            await ctx.send(post.url)
        elif "www.reddit.com/gallery" in post.url:
            await ctx.send(embed=embed, view=self.CustomUrl(post.url, "🖼 View Gallery"))
        else:
            embed.set_image(url=self.process_link(post.url))
            await ctx.send(embed=embed)

    @commands.hybrid_command(name='nsfw', description='Get a random nsfw post from a subreddit', )
    @app_commands.describe(posts="Number of posts to fetch (<15)")
    @commands.is_nsfw()
    async def nsfw(self, ctx: commands.Context, posts: int = 1) -> None:
        if posts > 16:
            await ctx.send("You can only fetch up to 15 posts at a time.", ephemeral=True)
            return
        await ctx.defer()
        nsfw_sub_list = ("curvy", "sexygirls", "TittyDrop", "nudes", "slut", "amateur", "legalteens", "realgirls", "collegesluts", "nsfw", "snapleaks",)
        subreddit = random.choice(nsfw_sub_list)
        posts = await self.get_random_posts(subreddit, "week", limit=posts, over_18=True)
        for post in posts:
            embed = discord.Embed(title=post.title, colour=0xFF5700)
            embed.set_author(name=f"Uploaded by u/{post.author} on {post.subreddit_name_prefixed}", url=f"https://reddit.com{post.permalink}")
            embed.set_footer(text=f"Requested by: {ctx.author.display_name}")
            if any(vid in post.url for vid in gif_sites):
                await ctx.send(embed=embed)
                await ctx.send(post.url)
            elif "www.reddit.com/gallery" in post.url:
                await ctx.send(embed=embed, view=self.CustomUrl(post.url, "🖼 View Gallery"))
            else:
                embed.set_image(url=self.process_link(post.url))
                await ctx.send(embed=embed)


async def setup(bot: AssistantBot):
    r = RedditConfig()
    if not r:
        bot.logger.warning("Reddit config not found. Reddit commands will not work.")
        return
    reddit = praw.Reddit(client_id=r.CLIENT_ID, client_secret=r.CLIENT_SECRET, username=r.USERNAME, password=r.PASSWORD, user_agent="discord:assistant:v1.0.0 (by u/andrew264)")
    await bot.add_cog(RedditCommands(bot, reddit))
