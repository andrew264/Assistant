import math

import disnake
from disnake import (
    Embed,
    Message,
    ButtonStyle,
    Button,
    Interaction
)
from disnake.ext import commands
from lavalink import DefaultPlayer as Player


class Queue(commands.Cog):
    def __init__(self, client: disnake.Client):
        self.client = client

    # Queue
    @commands.command(aliases=["q"])
    @commands.guild_only()
    async def queue(self, ctx: commands.Context) -> None:
        player: Player = self.client.lavalink.player_manager.get(ctx.guild.id)

        class QueuePages(disnake.ui.View):
            def __init__(self):
                super().__init__(timeout=180.0)
                self.page_no = 1
                self.message: Message | None = None

            async def on_timeout(self):
                await self.message.delete()
                self.stop()

            @disnake.ui.button(emoji="◀", style=ButtonStyle.secondary)
            async def prev_page(self, button: Button, interaction: Interaction):
                if self.page_no > 1:
                    self.page_no -= 1
                else:
                    self.page_no = math.ceil(len(player.queue) / 4)
                await interaction.response.edit_message(embed=self.QueueEmbed, view=self)

            @disnake.ui.button(emoji="▶", style=ButtonStyle.secondary)
            async def next_page(self, button: Button, interaction: Interaction):
                if self.page_no < math.ceil(len(player.queue) / 4):
                    self.page_no += 1
                else:
                    self.page_no = 1
                await interaction.response.edit_message(embed=self.QueueEmbed, view=self)

            @property
            def QueueEmbed(self) -> Embed:
                first = (self.page_no * 4) - 4
                if (self.page_no * 4) + 1 <= len(player.queue):
                    last = (self.page_no * 4)
                else:
                    last = len(player.queue)
                song_index = [i for i in range(first, last)]
                if not player.current:
                    return Embed(title="Queue is Empty", colour=0xFFA31A)
                embed = Embed(
                    title="Now Playing", colour=0xFFA31A,
                    description=f"{str(player.current)}", )
                if len(player.queue) >= 1:
                    next_songs = "\u200b"
                    max_page = math.ceil(len(player.queue) / 4)
                    for i in song_index:
                        next_songs += f"{i + 1}. {str(player.queue[i])}\n"
                    embed.add_field(name=f"Next Up ({self.page_no}/{max_page})", value=next_songs, inline=False)
                if player.repeat:
                    embed.set_footer(text=f"Looping through {len(player.queue) + 1} Songs")
                else:
                    embed.set_footer(text=f"{len(player.queue) + 1} Songs in Queue")
                return embed

        await ctx.message.delete()
        view = QueuePages()
        view.message = await ctx.send(embed=view.QueueEmbed, view=view)

    @queue.before_invoke
    async def check_voice(self, ctx: commands.Context) -> None:
        player: Player = self.client.lavalink.player_manager.get(ctx.guild.id)
        if ctx.voice_client is None or not player.is_connected:
            raise commands.CheckFailure("Bot is not connect to VC.")
        if ctx.author.voice is None:
            raise commands.CheckFailure("You are not connected to a voice channel.")
        if ctx.voice_client is not None and ctx.author.voice is not None:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                raise commands.CheckFailure("You must be in same VC as Bot.")


def setup(client):
    client.add_cog(Queue(client))
