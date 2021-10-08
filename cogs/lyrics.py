# Imports
import disnake
from disnake.ext import commands
from disnake import Spotify, Embed, Member, Client
from disnake.utils import get
from disnake import ActionRow, Button, ButtonStyle, Interaction, Option, OptionType, ApplicationCommandInteraction, MessageInteraction

from EnvVariables import GENIUS_TOKEN

from lyricsgenius import Genius
from lyricsgenius.types import Song
import re, asyncio

genius = Genius(GENIUS_TOKEN, verbose=False)

class LyricsProcess():

    def __init__(self):
        pass

    def SongTolist(song: Song):
        lyrics = re.sub(r"[0-9]*EmbedShare*",'',song.lyrics)
        lyricsList = list(lyrics.split("\n\n"))
        return lyricsList

    def fetchlyrics(song_title, artist_name):
        song = genius.search_song(song_title, artist_name)
        if song is not None and song.lyrics is not None:
            return song

    def generate_embed(title, track_url, album_art, lyricsList: list, pgno:int):
        embed = Embed(title = f'{title} ({pgno+1}/{len(lyricsList)})', url= track_url, color=0x1DB954, description=lyricsList[pgno])
        embed.set_thumbnail(url = album_art)
        return embed

class Pages(disnake.ui.View):
    def __init__(self, title: str, track_url: str, album_art: str, lyricsList: list):
        super().__init__()
        self.page_no = 0
        self.timeout = 360
        self.title = title
        self.track_url = track_url
        self.album_art = album_art
        self.lyricsList = lyricsList

    @disnake.ui.button(label='◀️', style=ButtonStyle.blurple)
    async def prev_page(self, button: Button, interaction: Interaction):
        if self.page_no > 0:
            self.page_no -= 1
        else: self.page_no = len(self.lyricsList)-1

        await interaction.response.edit_message(embed=LyricsProcess.generate_embed(title=self.title, track_url=self.track_url, album_art=self.album_art, lyricsList=self.lyricsList, pgno=self.page_no),view=self)

    @disnake.ui.button(label='▶️', style=ButtonStyle.blurple)
    async def next_page(self, button: Button, interaction: Interaction):
        if self.page_no < len(self.lyricsList)-1:
            self.page_no += 1
        else: self.page_no = 0
        
        await interaction.response.edit_message(embed=LyricsProcess.generate_embed(title=self.title, track_url=self.track_url, album_art=self.album_art, lyricsList=self.lyricsList, pgno=self.page_no),view=self)

class Lyrics(commands.Cog):

    def __init__(self, client: Client):
        self.client = client

    @commands.slash_command(description="Get Lyrics for the song you are currently listening to.",
                                options=[Option("title", "Song Title", OptionType.string),
                                         Option("author", "Song Author", OptionType.string) ])
    async def lyrics(self, inter: ApplicationCommandInteraction, title: str = None, author: str = ""):
        self.page_no = 0
        await inter.response.defer()
        loop = asyncio.get_event_loop()
        user: Member = get(self.client.get_all_members(), id=inter.author.id)
        if title is not None:
            song: Song = await loop.run_in_executor(None, LyricsProcess.fetchlyrics, title, author)
            title, track_url, album_art = song.title, song.url, song.song_art_image_url
        else:        
            for activity in user.activities:
                if isinstance(activity, Spotify):
                    title = re.sub(r'\([^)]*\)', '', activity.title)
                    author, track_url, album_art = activity.artist, activity.track_url, activity.album_cover_url
                    song = await loop.run_in_executor(None, LyricsProcess.fetchlyrics, title, author)

        if isinstance(song, Song) is False: return await inter.edit_original_message("Lyrics not Found :(")
        else:
            lyricsList = LyricsProcess.SongTolist(song)
            await inter.edit_original_message(embed = LyricsProcess.generate_embed(title=title, track_url=track_url, album_art=album_art, lyricsList=lyricsList, pgno=0), view=Pages(title=title, track_url=track_url, album_art=album_art, lyricsList=lyricsList))

def setup(client):
    client.add_cog(Lyrics(client))
