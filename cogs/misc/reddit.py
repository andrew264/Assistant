# Imports
import random
from typing import Optional, Any

import asyncpraw as praw
from asyncpraw.models import Submission
import disnake
from disnake.ext import commands
from disnake.ext.commands import Param

from EnvVariables import R_CLI, R_PAS, R_SEC, R_USR, Owner_ID
from assistant import Client

reddit_ins = praw.Reddit(
    client_id=R_CLI,
    client_secret=R_SEC,
    username=R_USR,
    password=R_PAS,
    user_agent="discord:prob_bot:v1.0.0 (by u/andrew264)",
)

gif_sites = ("redgifs.com", "v.redd.it", "imgur.com")


class Reddit(commands.Cog):
    def __init__(self, client: Client):
        self.client = client
        self._r_cache: dict[str, [Submission]] = {}

    async def get_random_posts(self, subreddit: str, uploaded: str,
                              limit: Optional[int] = 1, over_18:bool = False) -> list[Submission]:
        subreddit = await reddit_ins.subreddit(subreddit)
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

    @commands.slash_command(description="Fetch a NSFW Post from Reddit")
    async def nsfw(self, inter: disnake.ApplicationCommandInteraction,
                   posts: int = Param(description="Number of posts to fetch", default=1),
                   subreddit: str = Param(description="Enter a subreddit (Optional)", default=None), ) -> None:
        if isinstance(inter.channel, disnake.TextChannel) and inter.channel.is_nsfw() is False:
            await inter.response.send_message("This command is only available in NSFW channels.", ephemeral=True)
            return
        if posts > 16 or posts < 1:
            if inter.author.id != Owner_ID:
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
    client.add_cog(Reddit(client))
