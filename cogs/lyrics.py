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
    Member,
    Spotify,
    )
from disnake.utils import get
import disnake

from EnvVariables import GENIUS_TOKEN

from lyricsgenius import Genius
from lyricsgenius.types import Song
import re, asyncio

genius = Genius(GENIUS_TOKEN, verbose=False)

class LyricsProcess():

    def __init__(self):
        pass

    def SongTolist(song: Song) -> list[str]:
        lyrics = re.sub(r"[0-9]*EmbedShare*",'',song.lyrics)
        lyrics = re.sub(r"URLCopyEmbedCopy",'',lyrics)
        lyricsList = list(lyrics.split("\n\n"))
        return lyricsList

    def fetchlyrics(song_title: str, artist_name: str) -> Song:
        song = genius.search_song(song_title, artist_name)
        if song is not None and song.lyrics is not None:
            return song

    def generate_embed(title: str,
                       track_url: str,
                       album_art: str,
                       lyricsList: list,
                       avatar: str,
                       pgno: int) -> Embed:
        embed = Embed(title = f'{title}', url=track_url, color=0x1DB954, description=lyricsList[pgno])
        embed.set_thumbnail(url = album_art)
        embed.set_footer(text = f'({pgno+1}/{len(lyricsList)})', icon_url = avatar) 
        return embed

class Pages(disnake.ui.View):
    def __init__(self, song: Song, lyricsList: list[str]):
        super().__init__(timeout=180.0)
        self.page_no = 0
        self.song = song
        self.lyricsList = lyricsList

    async def on_timeout(self):
        await self.inter.edit_original_message(view=None)
        self.stop()

    @disnake.ui.button(label='◀️', style=ButtonStyle.blurple)
    async def prev_page(self, button: Button, interaction: Interaction) -> None:
        if self.page_no > 0:
            self.page_no -= 1
        else: self.page_no = len(self.lyricsList)-1
        await interaction.response.edit_message(embed=LyricsProcess.generate_embed(title=self.song.title,
                                                                                   track_url=self.song.url,
                                                                                   album_art=self.song.song_art_image_url,
                                                                                   lyricsList=self.lyricsList,
                                                                                   avatar=self.avatar,
                                                                                   pgno=self.page_no), view=self)

    @disnake.ui.button(label='▶️', style=ButtonStyle.blurple)
    async def next_page(self, button: Button, interaction: Interaction) -> None:
        if self.page_no < len(self.lyricsList)-1:
            self.page_no += 1
        else: self.page_no = 0
        await interaction.response.edit_message(embed=LyricsProcess.generate_embed(title=self.song.title,
                                                                                   track_url=self.song.url,
                                                                                   album_art=self.song.song_art_image_url,
                                                                                   lyricsList=self.lyricsList,
                                                                                   avatar=self.avatar,
                                                                                   pgno=self.page_no), view=self)

class Lyrics(commands.Cog):

    def __init__(self, client: Client):
        self.client = client

    @commands.slash_command(description="Get Lyrics for the song you are currently listening to.")
    async def lyrics(self,
                     inter: ApplicationCommandInteraction,
                     title: str = Param(description="Song Title", default=None),
                     author: str = Param(description="Song Author", default="")) -> None:
        await inter.response.defer()
        loop = asyncio.get_event_loop()
        user: Member = get(self.client.get_all_members(), id=inter.author.id)
        song: Song = None
        if title is not None:
            song: Song = await loop.run_in_executor(None, LyricsProcess.fetchlyrics, title, author)
        else:        
            for activity in user.activities:
                if isinstance(activity, Spotify):
                    title = re.sub(r'\([^)]*\)', '', activity.title)
                    song: Song = await loop.run_in_executor(None, LyricsProcess.fetchlyrics, title, activity.artist)
                    if hasattr(song, 'url'): song.url = activity.track_url

        if song is None:
            return await inter.edit_original_message("Lyrics not Found :(")
        else:
            lyricsList = LyricsProcess.SongTolist(song)
            MyPages = Pages(song, lyricsList)
            MyPages.inter = inter
            MyPages.avatar = inter.author.default_avatar.url
            await inter.edit_original_message(embed = LyricsProcess.generate_embed(title=song.title,
                                                                                   track_url=song.url,
                                                                                   album_art=song.song_art_image_url,
                                                                                   lyricsList=lyricsList,
                                                                                   avatar=inter.author.default_avatar.url,
                                                                                   pgno=0),
                                              view = MyPages)

def setup(client):
    client.add_cog(Lyrics(client))
