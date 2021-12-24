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
from disnake.utils import get
from lyricsgenius import Genius
from lyricsgenius.types import Song

from EnvVariables import GENIUS_TOKEN

genius = Genius(GENIUS_TOKEN, verbose=False)


def song_to_list(song: Song) -> list[str]:
    lyrics = re.sub(r"[0-9]*EmbedShare*", "", song.lyrics)
    lyrics = re.sub(r"URLCopyEmbedCopy", "", lyrics)
    lyrics_list = list(lyrics.split("\n\n"))
    return lyrics_list


def fetch_lyrics(song_title: str, artist_name: str) -> Song | None:
    song = genius.search_song(song_title, artist_name)
    if song and song.lyrics:
        return song
    return None


class SongInfo:
    def __init__(self, title: str, track_url: str, album_art: str, lyrics_list: list, avatar: str) -> None:
        self.title = title
        self.track_url = track_url
        self.album_art = album_art
        self.lyrics_list = lyrics_list
        self.avatar = avatar

    def generate_embed(self, pg_no: int, ) -> Embed:
        embed = Embed(title=f"{self.title}", url=self.track_url, color=0x1DB954, description=self.lyrics_list[pg_no])
        embed.set_thumbnail(url=self.album_art)
        embed.set_footer(text=f"({pg_no + 1}/{len(self.lyrics_list)})", icon_url=self.avatar)
        return embed


class Pages(disnake.ui.View):
    def __init__(self, song_info: SongInfo):
        super().__init__(timeout=180.0)
        self.page_no = 0
        self.song_info = song_info
        self.inter: ApplicationCommandInteraction | None = None

    async def on_timeout(self):
        await self.inter.edit_original_message(view=None)
        self.stop()

    @disnake.ui.button(label="◀", style=ButtonStyle.blurple)
    async def prev_page(self, button: Button, interaction: Interaction) -> None:
        if self.page_no > 0:
            self.page_no -= 1
        else:
            self.page_no = len(self.song_info.lyrics_list) - 1
        await interaction.response.edit_message(embed=self.song_info.generate_embed(self.page_no), view=self, )

    @disnake.ui.button(label="▶", style=ButtonStyle.blurple)
    async def next_page(self, button: Button, interaction: Interaction) -> None:
        if self.page_no < len(self.song_info.lyrics_list) - 1:
            self.page_no += 1
        else:
            self.page_no = 0
        await interaction.response.edit_message(embed=self.song_info.generate_embed(self.page_no), view=self, )


class Lyrics(commands.Cog):
    def __init__(self, client: Client):
        self.client = client

    @commands.slash_command(
        description="Get Lyrics for the song you are currently listening to."
    )
    async def lyrics(
            self,
            inter: ApplicationCommandInteraction,
            title: str = Param(description="Song Title", default=None),
            author: str = Param(description="Song Author", default=""),
    ) -> None:

        await inter.response.defer()

        song = None
        loop = asyncio.get_event_loop()
        if title:
            song = await loop.run_in_executor(None, fetch_lyrics, title, author)
        else:
            user = get(self.client.get_all_members(), id=inter.author.id)
            if user is None:
                return
            for activity in user.activities:
                if isinstance(activity, Spotify):
                    title = re.sub(r"\([^)]*\)", "", activity.title)
                    song = await loop.run_in_executor(None, fetch_lyrics, title, activity.artist)
                    if isinstance(song, Song) and hasattr(song, "url"):
                        song.url = activity.track_url
                    break

        if song is None:
            await inter.edit_original_message(content="Lyrics not Found :(")
            return

        song_info: SongInfo = SongInfo(title=title,
                                       track_url=song.url,
                                       album_art=song.song_art_image_url,
                                       lyrics_list=song_to_list(song),
                                       avatar=inter.author.display_avatar.url, )

        my_pages = Pages(song_info)
        my_pages.inter = inter
        await inter.edit_original_message(embed=song_info.generate_embed(0), view=my_pages, )


def setup(client):
    client.add_cog(Lyrics(client))
