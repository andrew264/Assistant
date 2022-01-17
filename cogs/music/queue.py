import math

import disnake
from disnake import (
    Embed,
    Message,
    ButtonStyle,
    Button,
    Interaction
)
from lavalink import DefaultPlayer


def QueueEmbed(player: DefaultPlayer, page_no: int) -> Embed:
    first = (page_no * 4) - 4
    if (page_no * 4) + 1 <= len(player.queue):
        last = (page_no * 4)
    else:
        last = len(player.queue)
    song_index = [i for i in range(first, last)]
    if not player.current:
        return Embed(title="Queue is Empty", colour=0xFFA31A)
    embed = Embed(
        title="Now Playing", colour=0xFFA31A,
        description=f"[{player.current.Title}]({player.current.pURL} \"by {player.current.Author.display_name}\")", )
    if len(player.queue) >= 1:
        next_songs = "\u200b"
        max_page = math.ceil(len(player.queue) / 4)
        for i in song_index:
            next_songs += f"{i + 1}. [{player.queue[i].Title}]({player.queue[i].pURL} \"by {player.queue[i].Author.display_name}\")\n"
        embed.add_field(name=f"Next Up ({page_no}/{max_page})", value=next_songs, inline=False)
    avatar_url = player.current.Author.display_avatar.url
    if player.repeat:
        embed.set_footer(text=f"Looping through {len(player.queue) + 1} Songs", icon_url=avatar_url)
    else:
        embed.set_footer(text=f"{len(player.queue) + 1} Songs in Queue", icon_url=avatar_url)
    return embed


class QueuePages(disnake.ui.View):
    def __init__(self, player):
        super().__init__(timeout=60.0)
        self.page_no = 1
        self.player = player
        self.message: Message | None = None

    async def on_timeout(self):
        await self.message.edit(view=None)
        self.stop()

    @disnake.ui.button(emoji="◀", style=ButtonStyle.secondary)
    async def prev_page(self, button: Button, interaction: Interaction):
        if self.page_no > 1:
            self.page_no -= 1
        else:
            self.page_no = math.ceil(len(self.player.queue) / 4)
        await interaction.response.edit_message(embed=QueueEmbed(self.player, self.page_no), view=self)

    @disnake.ui.button(emoji="▶", style=ButtonStyle.secondary)
    async def next_page(self, button: Button, interaction: Interaction):
        if self.page_no < math.ceil(len(self.player.queue) / 4):
            self.page_no += 1
        else:
            self.page_no = 1
        await interaction.response.edit_message(embed=QueueEmbed(self.player, self.page_no), view=self)
