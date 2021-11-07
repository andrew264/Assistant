# Imports
from disnake.ext import commands
from disnake.ext.commands import Param
from disnake import (
    ApplicationCommandInteraction,
    Button,
    ButtonStyle,
    Client,
    Embed,
    Interaction,
    Spotify,
)
from disnake.utils import get
import disnake

from EnvVariables import GENIUS_TOKEN

from lyricsgenius import Genius
from lyricsgenius.types import Song
import re, asyncio

genius = Genius(GENIUS_TOKEN, verbose=False)


def SongTolist(song: Song) -> list[str]:
    lyrics = re.sub(r"[0-9]*EmbedShare*", "", song.lyrics)
    lyrics = re.sub(r"URLCopyEmbedCopy", "", lyrics)
    lyricsList = list(lyrics.split("\n\n"))
    return lyricsList


def fetchlyrics(song_title: str, artist_name: str) -> Song | None:
    song = genius.search_song(song_title, artist_name)
    if song and song.lyrics:
        return song
    return None


def generate_embed(
    title: str, track_url: str, album_art: str, lyricsList: list, avatar: str, pgno: int
) -> Embed:
    embed = Embed(
        title=f"{title}", url=track_url, color=0x1DB954, description=lyricsList[pgno]
    )
    embed.set_thumbnail(url=album_art)
    embed.set_footer(text=f"({pgno+1}/{len(lyricsList)})", icon_url=avatar)
    return embed


class Pages(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=180.0)
        self.page_no = 0
        self.song: Song
        self.lyricsList: list[str]
        self.inter: ApplicationCommandInteraction
        self.display_avatar: str

    async def on_timeout(self):
        await self.inter.edit_original_message(view=None)
        self.stop()

    @disnake.ui.button(label="◀️", style=ButtonStyle.blurple)
    async def prev_page(self, button: Button, interaction: Interaction) -> None:
        if self.page_no > 0:
            self.page_no -= 1
        else:
            self.page_no = len(self.lyricsList) - 1
        await interaction.response.edit_message(
            embed=generate_embed(
                title=self.song.title,
                track_url=self.song.url,
                album_art=self.song.song_art_image_url,
                lyricsList=self.lyricsList,
                avatar=self.display_avatar,
                pgno=self.page_no,
            ),
            view=self,
        )

    @disnake.ui.button(label="▶️", style=ButtonStyle.blurple)
    async def next_page(self, button: Button, interaction: Interaction) -> None:
        if self.page_no < len(self.lyricsList) - 1:
            self.page_no += 1
        else:
            self.page_no = 0
        await interaction.response.edit_message(
            embed=generate_embed(
                title=self.song.title,
                track_url=self.song.url,
                album_art=self.song.song_art_image_url,
                lyricsList=self.lyricsList,
                avatar=self.display_avatar,
                pgno=self.page_no,
            ),
            view=self,
        )


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

        user = get(self.client.get_all_members(), id=inter.author.id)
        if user is None:
            return

        song = None
        loop = asyncio.get_event_loop()
        if title:
            song = await loop.run_in_executor(None, fetchlyrics, title, author)
        else:
            for activity in user.activities:
                if isinstance(activity, Spotify):
                    title = re.sub(r"\([^)]*\)", "", activity.title)
                    song = await loop.run_in_executor(
                        None, fetchlyrics, title, activity.artist
                    )
                    if isinstance(song, Song) and hasattr(song, "url"):
                        song.url = activity.track_url
                    break

        if song is None:
            await inter.edit_original_message(content="Lyrics not Found :(")
            return
        else:
            lyricsList = SongTolist(song)
            MyPages = Pages()
            MyPages.lyricsList = lyricsList
            MyPages.song = song
            MyPages.inter = inter
            MyPages.display_avatar = inter.author.display_avatar.url
            await inter.edit_original_message(
                embed=generate_embed(
                    title=song.title,
                    track_url=song.url,
                    album_art=song.song_art_image_url,
                    lyricsList=lyricsList,
                    avatar=inter.author.display_avatar.url,
                    pgno=0,
                ),
                view=MyPages,
            )


def setup(client):
    client.add_cog(Lyrics(client))
