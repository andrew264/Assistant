# Imports
import asyncio
import re

import disnake
from disnake import (
    ApplicationCommandInteraction,
    Button,
    ButtonStyle,
    Client,
    Embed,
    Interaction,
    Spotify,
)
from disnake.ext import commands
from disnake.ext.commands import Param
from lyricsgenius import Genius
from lyricsgenius.types import Song

from EnvVariables import GENIUS_TOKEN

genius = Genius(GENIUS_TOKEN, verbose=False)


def fetch_lyrics(song_title: str, artist_name: str) -> Song | None:
    song = genius.search_song(song_title, artist_name)
    if song and song.lyrics:
        return song
    return None


class SongInfo:
    def __init__(self, song: Song, avatar_url: str) -> None:
        self.song = song
        self.title = song.title
        self.track_url = song.url
        self.album_art = song.song_art_image_url
        self.lyrics_list = self.song_to_list()
        self.avatar_url = avatar_url

    def song_to_list(self) -> list[str]:
        lyrics = re.sub(r"[0-9]*EmbedShare*", "", self.song.lyrics)
        lyrics = re.sub(r"URLCopyEmbedCopy", "", lyrics)
        lyrics_list = list(lyrics.split("\n\n"))
        return lyrics_list

    def generate_embed(self, pg_no: int, ) -> Embed:
        embed = Embed(title=f"{self.title}", url=self.track_url, color=0x1DB954, description=self.lyrics_list[pg_no])
        embed.set_thumbnail(url=self.album_art)
        embed.set_footer(text=f"({pg_no + 1}/{len(self.lyrics_list)})", icon_url=self.avatar_url)
        return embed


class Pages(disnake.ui.View):
    def __init__(self, song_info: SongInfo, inter: ApplicationCommandInteraction):
        super().__init__(timeout=120.0)
        self.page_no = 0
        self.song_info = song_info
        self.inter = inter

    async def on_timeout(self):
        await self.inter.edit_original_message(view=None)
        self.stop()

    @disnake.ui.button(emoji="◀", style=ButtonStyle.blurple)
    async def prev_page(self, button: Button, interaction: Interaction) -> None:
        if self.page_no > 0:
            self.page_no -= 1
        else:
            self.page_no = len(self.song_info.lyrics_list) - 1
        await interaction.response.edit_message(embed=self.song_info.generate_embed(self.page_no), view=self, )

    @disnake.ui.button(emoji="▶", style=ButtonStyle.blurple)
    async def next_page(self, button: Button, interaction: Interaction) -> None:
        if self.page_no < len(self.song_info.lyrics_list) - 1:
            self.page_no += 1
        else:
            self.page_no = 0
        await interaction.response.edit_message(embed=self.song_info.generate_embed(self.page_no), view=self, )


class Lyrics(commands.Cog):
    def __init__(self, client: Client):
        self.client = client

    @commands.slash_command(description="Get Lyrics for the song you are currently listening to.")
    async def lyrics(self, inter: ApplicationCommandInteraction,
                     title: str = Param(description="Song Title", default=None),
                     author: str = Param(description="Song Author", default=""), ) -> None:

        await inter.response.defer()

        loop = asyncio.get_event_loop()
        song: Song | None = None
        if title:
            song = await loop.run_in_executor(None, fetch_lyrics, title, author)
        else:
            for activity in inter.author.activities:
                if isinstance(activity, Spotify):
                    title = re.sub(r"\([^)]*\)", "", activity.title)
                    song = await loop.run_in_executor(None, fetch_lyrics, title, activity.artist)
                    if isinstance(song, Song) and hasattr(song, "url"):
                        song.url = activity.track_url
                    break

        if song is None:
            await inter.edit_original_message(content="Lyrics not Found :(")
            return

        song_info: SongInfo = SongInfo(song, inter.author.display_avatar.url, )
        my_pages = Pages(song_info, inter)
        await inter.edit_original_message(embed=song_info.generate_embed(0), view=my_pages, )


def setup(client):
    client.add_cog(Lyrics(client))
