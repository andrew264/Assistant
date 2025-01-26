import math
from typing import cast, Optional

import discord
import wavelink
from discord.ext import commands

from assistant import AssistantBot
from config import LavaConfig
from utils import check_same_vc, check_vc, clickable_song


class Queue(commands.Cog):
    def __init__(self, bot: AssistantBot):
        self.bot = bot

    @commands.hybrid_command(name="queue", aliases=["q"], description="View the queue")
    @commands.guild_only()
    @check_vc()
    @check_same_vc()
    async def queue(self, ctx: commands.Context):
        vc: wavelink.Player = cast(wavelink.Player, ctx.voice_client)  # type: ignore
        msg: Optional[discord.Message] = None

        class QueuePages(discord.ui.View):
            def __init__(self):
                super(QueuePages, self).__init__(timeout=180)
                self.page_no = 1

            async def on_timeout(self) -> None:
                assert msg is not None
                self.stop()
                await msg.edit(view=None)

            @discord.ui.button(emoji="◀", style=discord.ButtonStyle.secondary)
            async def prev_page(self, interaction: discord.Interaction, button: discord.Button):
                if self.page_no > 1:
                    self.page_no -= 1
                else:
                    self.page_no = math.ceil(vc.queue.count / 4)
                await interaction.response.edit_message(embed=self.embed, view=self)

            @discord.ui.button(emoji="▶", style=discord.ButtonStyle.secondary)
            async def next_page(self, interaction: discord.Interaction, button: discord.Button):
                if self.page_no < math.ceil(vc.queue.count / 4):
                    self.page_no += 1
                else:
                    self.page_no = 1
                await interaction.response.edit_message(embed=self.embed, view=self)

            @property
            def embed(self) -> discord.Embed:
                first = (self.page_no * 4) - 4
                if (self.page_no * 4) + 1 <= vc.queue.count:
                    last = (self.page_no * 4)
                else:
                    last = vc.queue.count
                song_index = [i for i in range(first, last)]
                if not vc.current:
                    return discord.Embed(title="Queue is Empty", colour=0xFFA31A)
                embed = discord.Embed(title="Now Playing", colour=0xFFA31A, description=f"{clickable_song(vc.current)}")
                if vc.queue.count > 0:
                    next_songs = "\u200b"
                    max_page = math.ceil(vc.queue.count / 4)
                    for i in song_index:
                        next_songs += f"{i + 1}. {clickable_song(vc.queue[i])}\n"
                    embed.add_field(name=f"Next Up ({self.page_no}/{max_page})", value=next_songs, inline=False)
                if vc.queue.mode is wavelink.QueueMode.loop_all:
                    embed.set_footer(text=f"Looping through {vc.queue.count + 1} Songs")
                else:
                    embed.set_footer(text=f"{vc.queue.count + 1} Songs in Queue")
                return embed

        v = QueuePages()
        msg = await ctx.send(embed=v.embed, view=v)


async def setup(bot: AssistantBot):
    if LavaConfig():
        await bot.add_cog(Queue(bot))
