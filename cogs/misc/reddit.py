# Imports
import random
from typing import Optional

import asyncpraw as praw
import disnake
from asyncpraw.models import Submission
from disnake.ext import commands
from disnake.ext.commands import Param

from assistant import Client
from config import RedditConfig, owner_id

gif_sites = ("redgifs.com", "v.redd.it", "imgur.com")


class Reddit(commands.Cog):
    def __init__(self, client: Client, reddit: praw.Reddit):
        self.client = client
        self._r_cache: dict[str, list[Submission]] = {}
        self.reddit = reddit

    async def get_random_posts(self, subreddit: str, uploaded: str,
                               limit: Optional[int] = 1, over_18: bool = False) -> list[Submission]:
        subreddit = await self.reddit.subreddit(subreddit)
        if subreddit.display_name not in self._r_cache:
            self._r_cache[subreddit.display_name] = []
            async for submission in subreddit.top(uploaded, limit=100):
                self._r_cache[subreddit.display_name].append(submission)
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

    class CustomUrl(disnake.ui.View):
        def __init__(self, url: str, label: str):
            super().__init__()
            self.add_item(disnake.ui.Button(style=disnake.ButtonStyle.link, label=label, url=url))

    @commands.slash_command(description="Fetch a meme from Reddit")
    @commands.guild_only()
    async def meme(self, inter: disnake.ApplicationCommandInteraction) -> None:
        await inter.response.send_message("Fetching posts...")
        sub_list = ("memes", "dankmemes", "funny")
        subreddit = random.choice(sub_list)
        post = (await self.get_random_posts(subreddit, "day"))[0]
        embed = disnake.Embed(title=post.title, colour=0xFF5700)
        embed.set_author(name=f"Uploaded by u/{post.author.name} on {post.subreddit_name_prefixed}",
                         url=f"https://reddit.com{post.permalink}")
        embed.set_footer(text=f"Requested by: {inter.author.display_name}")
        if any(vid in post.url for vid in gif_sites):
            await inter.edit_original_message(content="", embed=embed)
            await inter.followup.send(post.url)
        elif "www.reddit.com/gallery" in post.url:
            await inter.edit_original_message(content="", embed=embed, view=self.CustomUrl(post.url, "🖼 View Gallery"))
        else:
            embed.set_image(url=self.process_link(post.url))
            await inter.edit_original_message(content="", embed=embed)

    @commands.slash_command(description="Fetch a NSFW Post from Reddit", nsfw=True)
    async def nsfw(self, inter: disnake.ApplicationCommandInteraction,
                   posts: int = Param(description="Number of posts to fetch", default=1),
                   subreddit: str = Param(description="Enter a subreddit (Optional)", default=None), ) -> None:
        if posts > 16 or posts < 1:
            if inter.author.id != owner_id:
                await inter.response.send_message("Maximum of 15 posts at a time.", ephemeral=True)
                return
        await inter.response.send_message("Fetching posts...", ephemeral=True)
        nsfw_sub_list = ("curvy", "sexygirls", "TittyDrop",
                         "nudes", "slut", "amateur", "legalteens", "realgirls",
                         "collegesluts", "wifesharing", "snapleaks",)
        if subreddit is None:
            subreddit = random.choice(nsfw_sub_list)
        posts = await self.get_random_posts(subreddit, "week", limit=posts, over_18=True)
        for post in posts:
            embed = disnake.Embed(title=post.title, colour=0xFF5700)
            embed.set_author(name=f"Uploaded by u/{post.author} on {post.subreddit_name_prefixed}",
                             url=f"https://reddit.com{post.permalink}")
            embed.set_footer(text=f"Requested by: {inter.author.display_name}")
            if any(vid in post.url for vid in gif_sites):
                await inter.channel.send(embed=embed)
                await inter.channel.send(post.url)
            elif "www.reddit.com/gallery" in post.url:
                await inter.channel.send(embed=embed, view=self.CustomUrl(post.url, "🖼 View Gallery"))
            else:
                embed.set_image(url=self.process_link(post.url))
                await inter.channel.send(embed=embed)


def setup(client):
    r_conf = RedditConfig()
    reddit_ins = praw.Reddit(
        client_id=r_conf.client_id,
        client_secret=r_conf.client_secret,
        username=r_conf.username,
        password=r_conf.password,
        user_agent="discord:assistant:v1.0.0 (by u/andrew264)",
    ) if r_conf else None
    if reddit_ins is None:
        client.logger.warning("Reddit API not configured, Reddit commands will not be loaded.")
    else:
        client.add_cog(Reddit(client, reddit_ins))
