import math
from typing import cast, Optional

import discord
import wavelink
from discord import app_commands
from discord.ext import commands

from assistant import AssistantBot
from config import LAVA_CONFIG
from utils import check_same_vc, check_vc, clickable_song


class Queue(commands.Cog):
    def __init__(self, bot: AssistantBot):
        self.bot = bot

    def get_voice_client(self, ctx: commands.Context) -> wavelink.Player:  # helper
        vc = ctx.guild.voice_client
        if not vc:
            self.bot.logger.debug("[MUSIC] Creating a new voice client. idk why?")
            vc = ctx.author.voice.channel.connect(cls=wavelink.Player, self_deaf=True)
        return cast(wavelink.Player, vc)

    @commands.hybrid_group(name="queue", aliases=["q"], description="Manage the song queue.", invoke_without_command=True)
    @commands.guild_only()
    @check_vc()
    @check_same_vc()
    async def queue(self, ctx: commands.Context):
        """View the current queue."""
        vc: wavelink.Player = self.get_voice_client(ctx)
        await self.show_queue(ctx, vc)

    async def show_queue(self, ctx: commands.Context, vc: wavelink.Player):
        """Displays the current queue with pagination."""
        if not vc.current and vc.queue.is_empty:
            return await ctx.send("The queue is empty.")

        msg: Optional[discord.Message] = None

        class QueuePages(discord.ui.View):
            def __init__(self, vc: wavelink.Player):
                super(QueuePages, self).__init__(timeout=180)
                self.vc = vc
                self.page_no = 1

            async def on_timeout(self) -> None:
                if msg:  # Check if msg is not None
                    self.stop()
                    await msg.edit(view=None)

            @discord.ui.button(emoji="◀", style=discord.ButtonStyle.secondary)
            async def prev_page(self, interaction: discord.Interaction, button: discord.Button):
                if self.page_no > 1:
                    self.page_no -= 1
                else:
                    self.page_no = math.ceil(self.vc.queue.count / 4)
                await interaction.response.edit_message(embed=self.embed, view=self)

            @discord.ui.button(emoji="▶", style=discord.ButtonStyle.secondary)
            async def next_page(self, interaction: discord.Interaction, button: discord.Button):
                if self.page_no < math.ceil(self.vc.queue.count / 4):
                    self.page_no += 1
                else:
                    self.page_no = 1
                await interaction.response.edit_message(embed=self.embed, view=self)

            @property
            def embed(self) -> discord.Embed:
                first = (self.page_no * 4) - 4
                last = min((self.page_no * 4), self.vc.queue.count)
                song_index = range(first, last)

                if not self.vc.current:
                    return discord.Embed(title="Queue is Empty", colour=0xFFA31A)

                embed = discord.Embed(title="Now Playing", colour=0xFFA31A, description=f"{clickable_song(self.vc.current)}")

                if self.vc.queue.count > 0:
                    next_songs = "\n".join(f"{i + 1}. {clickable_song(self.vc.queue[i])}" for i in song_index)
                    max_page = math.ceil(self.vc.queue.count / 4)
                    embed.add_field(name=f"Next Up ({self.page_no}/{max_page})", value=next_songs or "\u200b", inline=False)

                loop_status = "Looping through all songs" if self.vc.queue.mode is wavelink.QueueMode.loop_all else "Looping Current Song" if self.vc.queue.mode is wavelink.QueueMode.loop else "Loop Disabled"
                embed.set_footer(text=f"{loop_status} | {self.vc.queue.count + 1} Songs in Queue")
                return embed

        v = QueuePages(vc)
        msg = await ctx.send(embed=v.embed, view=v)

    @queue.command(name="remove", aliases=["rm"], description="Remove a song from the queue by index.")
    @app_commands.describe(index="The index of the song to remove.")
    @check_vc()
    @check_same_vc()
    async def remove(self, ctx: commands.Context, index: int):
        """Remove a song from the queue by its index."""
        vc = self.get_voice_client(ctx)

        if vc.queue.is_empty:
            return await ctx.send("The queue is empty.")

        if not 1 <= index <= vc.queue.count:
            return await ctx.send("Invalid index.  Use `/queue` to see the queue with indexes.")

        removed_song = vc.queue.peek(index - 1)
        vc.queue.delete(index-1)
        await ctx.send(f"Removed {clickable_song(removed_song)} from the queue.", suppress_embeds=True)

    @queue.command(name="clear", description="Clear the entire queue.")
    @check_vc()
    @check_same_vc()
    async def clear(self, ctx: commands.Context):
        """Clear the entire queue."""
        vc = self.get_voice_client(ctx)

        if vc.queue.is_empty:
            return await ctx.send("The queue is already empty.")

        vc.queue.clear()
        await ctx.send("Queue cleared.")

    @queue.command(name="shuffle", aliases=["sh"], description="Shuffle the queue.")
    @check_vc()
    @check_same_vc()
    async def shuffle(self, ctx: commands.Context):
        """Shuffle the queue."""
        vc = self.get_voice_client(ctx)

        if vc.queue.is_empty:
            return await ctx.send("The queue is empty.")

        if vc.queue.count < 2:
            return await ctx.send("Not enough songs in queue to shuffle")

        vc.queue.shuffle()
        await ctx.send("Queue shuffled.")
        await self.show_queue(ctx, vc)  # Show updated queue

    @queue.command(name="move", aliases=["mv"], description="Move a song within the queue.")
    @app_commands.describe(from_index="The current index of the song.", to_index="The new index of the song.")
    @check_vc()
    @check_same_vc()
    async def move(self, ctx: commands.Context, from_index: int, to_index: int):
        """Move a song from one position in the queue to another."""
        vc = self.get_voice_client(ctx)

        if vc.queue.is_empty:
            return await ctx.send("The queue is empty.")

        if not (1 <= from_index <= vc.queue.count and 1 <= to_index <= vc.queue.count):
            return await ctx.send("Invalid index(es). Use `/queue` to see the queue.")

        if from_index == to_index:
            return await ctx.send("Song is already in that position.")
        try:
            song = vc.queue.peek(from_index-1)
            vc.queue.swap(from_index-1, to_index-1)
            await ctx.send(f"Moved {clickable_song(song)} from position `{from_index}` to `{to_index}`.", suppress_embeds=True)
            await self.show_queue(ctx, vc)
        except IndexError:
            await ctx.send("Invalid index(es). Please ensure both from_index and to_index are within the queue bounds.")

    @queue.command(name="loop", aliases=["l"], description="Toggles the loop mode of the queue.")
    async def loop_queue(self, ctx: commands.Context) -> None:
        """Toggle queue looping."""
        vc: wavelink.Player = self.get_voice_client(ctx)

        if not vc.current:
            await ctx.send("Nothing is playing.")
            return

        match vc.queue.mode:
            case wavelink.QueueMode.loop_all:
                vc.queue.mode = wavelink.QueueMode.normal
                await ctx.send("Queue loop disabled.")
            case wavelink.QueueMode.normal:
                vc.queue.mode = wavelink.QueueMode.loop_all
                await ctx.send("Queue loop enabled.")
            case _:  # shouldn't happen
                vc.queue.mode = wavelink.QueueMode.normal
                await ctx.send("Queue loop disabled. (Unexpected state)")

        await self.show_queue(ctx, vc)


async def setup(bot: AssistantBot):
    if LAVA_CONFIG:
        await bot.add_cog(Queue(bot))
