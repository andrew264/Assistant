import asyncio
import logging
import random
from dataclasses import dataclass
from typing import List, Optional

import asyncpraw as praw
import discord
from asyncpraw.models import Submission
from cachetools import TTLCache
from discord import app_commands, ui
from discord.ext import commands

from assistant import AssistantBot
from config import REDDIT_CONFIG

REDDIT_ORANGE = 0xFF5700
CACHE_SIZE = 2000
CACHE_TTL = 3600
MAX_POSTS = 5
DEFAULT_TIME_FILTER = "week"

VIDEO_DOMAINS = {"redgifs.com", "v.redd.it", "imgur.com"}
GALLERY_DOMAIN = "www.reddit.com/gallery"

logger = logging.getLogger(__name__)

reddit_cache = TTLCache(maxsize=CACHE_SIZE, ttl=CACHE_TTL)


@dataclass
class RedditPost:
    submission: Submission
    content_url: str
    is_gallery: bool
    is_video: bool


class RedditClient:
    def __init__(self, config: REDDIT_CONFIG):
        self.instance = praw.Reddit(client_id=config.client_id, client_secret=config.client_secret, username=config.username, password=config.password,
                                    user_agent=f"discord:assistant:v1.0.0 (by u/{config.username})")

    async def fetch_posts(self, subreddit: str, time_filter: str = DEFAULT_TIME_FILTER, limit: int = 100, over18: bool = False) -> List[Submission]:
        cache_key = f"{subreddit}:{time_filter}"
        if cached := reddit_cache.get(cache_key):
            return cached

        try:
            sub = await self.instance.subreddit(subreddit)
            posts = [post async for post in sub.top(time_filter, limit=limit) if post.over_18 == over18]
            reddit_cache[cache_key] = posts
            return posts
        except Exception as e:
            logger.error(f"Failed to fetch posts from r/{subreddit}: {e}")
            return []


class RedditView(ui.View):
    def __init__(self, post: Submission):
        super().__init__(timeout=120)
        self.add_item(ui.Button(label="View Post", url=f"https://reddit.com{post.permalink}"))
        if post.is_gallery:
            self.add_item(ui.Button(label="View Gallery", url=post.url))


class RedditCommands(commands.Cog):
    MEME_SUBS = ("memes", "dankmemes", "funny", "me_irl")
    NSFW_SUBS = ("sexygirls", "TittyDrop", "nudes", "legalteens", "realgirls", "collegesluts", "nsfw", "rule34", "celebnsfw", "boobies", "nostalgiafapping")

    def __init__(self, bot: AssistantBot):
        self.bot = bot
        self.reddit = RedditClient(REDDIT_CONFIG) if REDDIT_CONFIG else None

    async def _process_post(self, submission: Submission) -> Optional[RedditPost]:
        """Process a submission into a RedditPost dataclass"""
        if not submission.url:
            return None

        content_url = submission.url
        if content_url.endswith(".gifv"):
            content_url = content_url[:-1]

        return RedditPost(submission=submission, content_url=content_url, is_gallery=GALLERY_DOMAIN in content_url, is_video=any(domain in content_url for domain in VIDEO_DOMAINS))

    async def _send_post(self, ctx: commands.Context, post: RedditPost):
        """Handle post display logic"""
        embed = discord.Embed(title=post.submission.title[:256], color=REDDIT_ORANGE, url=f"https://reddit.com{post.submission.permalink}")

        author = post.submission.author
        embed.set_author(name=f"u/{author.name}" if author else "Deleted User", icon_url=None)

        embed.set_footer(text=f"r/{post.submission.subreddit.display_name} | 👍 {post.submission.score}")

        if post.is_video:
            await ctx.send(embed=embed)
            await ctx.send(post.content_url)
        elif post.is_gallery:
            await ctx.send(embed=embed, view=RedditView(post.submission))
        else:
            embed.set_image(url=post.content_url)
            await ctx.send(embed=embed)

    async def _get_random_posts(self, subreddit: str, time_filter: str, nsfw: bool, limit: int) -> List[RedditPost]:
        """Retrieve and process random posts from specified subreddit"""
        if not self.reddit:
            raise ValueError("Reddit client not configured")

        posts = await self.reddit.fetch_posts(subreddit, time_filter, over18=nsfw)
        valid_posts = [await self._process_post(p) for p in posts]
        valid_posts = [p for p in valid_posts if p is not None]

        return random.sample(valid_posts, min(limit, len(valid_posts)))

    @commands.hybrid_command(name="meme", description="Get fresh memes from popular subreddits")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @app_commands.describe(count="Number of memes to fetch (max 5)")
    async def meme_command(self, ctx: commands.Context, count: app_commands.Range[int, 1, MAX_POSTS] = 1):
        """Fetch memes from popular subreddits"""
        await ctx.defer()
        subreddit = random.choice(self.MEME_SUBS)

        try:
            posts = await self._get_random_posts(subreddit, DEFAULT_TIME_FILTER, False, count)
            if not posts:
                return await ctx.send("🚫 Couldn't find any suitable memes", delete_after=15)

            for post in posts:
                await self._send_post(ctx, post)
                await asyncio.sleep(1)  # Rate limit protection

        except Exception as e:
            logger.error(f"Meme command error: {e}")
            await ctx.send("❌ Failed to fetch memes. Try again later.", delete_after=15)

    @commands.hybrid_command(name="nsfw", description="Fetch NSFW content from Reddit")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @app_commands.describe(count="Number of posts to fetch (max 5)")
    @commands.is_nsfw()
    async def nsfw_command(self, ctx: commands.Context, count: app_commands.Range[int, 1, MAX_POSTS] = 1):
        """Fetch NSFW content from Reddit"""
        await ctx.defer()
        subreddit = random.choice(self.NSFW_SUBS)

        try:
            posts = await self._get_random_posts(subreddit, DEFAULT_TIME_FILTER, True, count)
            if not posts:
                return await ctx.send("🚫 No content found", delete_after=15)

            for post in posts:
                await self._send_post(ctx, post)
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"NSFW command error: {e}")
            await ctx.send("❌ Failed to fetch content. Try again later.", delete_after=15)


async def setup(bot: AssistantBot):
    if not REDDIT_CONFIG:
        bot.logger.warning("Reddit credentials missing - commands disabled")
        return

    await bot.add_cog(RedditCommands(bot))
