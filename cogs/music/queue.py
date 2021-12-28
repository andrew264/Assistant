import math

import disnake
from disnake import (
    Embed,
    Message,
    ButtonStyle,
    Button,
    Interaction
)


def QueueEmbed(song_list: list, page_no) -> Embed:
    first = (page_no * 4) - 3
    if (page_no * 4) + 1 <= len(song_list):
        last = (page_no * 4) + 1
    else:
        last = len(song_list)
    song_index = [i for i in range(first, last)]
    if not song_list:
        return Embed(title="Queue is Empty", colour=0xFFA31A)
    embed = Embed(
        title="Now Playing",
        description=f"[{song_list[0].Title}]({song_list[0].pURL} \"by {song_list[0].Author}\")",
        colour=0xFFA31A,
    )
    if len(song_list) > 1:
        next_songs = "\u200b"
        max_page = math.ceil((len(song_list) - 1) / 4)
        for i in song_index:
            next_songs += f"{i}. [{song_list[i].Title}]({song_list[i].pURL} \"by {song_list[i].Author}\")\n"
        embed.add_field(name=f"Next Up ({page_no}/{max_page})", value=next_songs, inline=False)
    return embed


class QueuePages(disnake.ui.View):
    def __init__(self, obj):
        super().__init__(timeout=60.0)
        self.page_no = 1
        self.obj = obj
        self.message: Message | None = None

    async def on_timeout(self):
        await self.message.edit(view=None)
        self.stop()

    @disnake.ui.button(emoji="◀", style=ButtonStyle.secondary)
    async def prev_page(self, button: Button, interaction: Interaction):
        if self.page_no > 1:
            self.page_no -= 1
        else:
            self.page_no = math.ceil((len(self.obj) - 1) / 4)
        await interaction.response.edit_message(embed=QueueEmbed(self.obj, self.page_no), view=self)

    @disnake.ui.button(emoji="▶", style=ButtonStyle.secondary)
    async def next_page(self, button: Button, interaction: Interaction):
        if self.page_no < math.ceil((len(self.obj) - 1) / 4):
            self.page_no += 1
        else:
            self.page_no = 1
        await interaction.response.edit_message(embed=QueueEmbed(self.obj, self.page_no), view=self)
