from discord.ext import commands
from discord import Spotify, Embed, Member
from discord.utils import get
from lyricsgenius import Genius
from lyricsgenius.types import Song
import re, asyncio
from dislash import ActionRow, Button, ButtonStyle, Option, OptionType
from dislash.interactions import SlashInteraction, MessageInteraction
from dislash.application_commands import slash_client
from olenv import GENIUS_TOKEN

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

class Lyrics(commands.Cog):

    def __init__(self,client):
        self.client = client

    @slash_client.slash_command(description="Get Lyrics for the song you are currently listening to.",
                                options=[Option("title", "Song Title", OptionType.STRING),
                                         Option("author", "Song Author", OptionType.STRING) ])
    async def lyrics(self, inter: SlashInteraction, title: str = None, author: str = ""):
        self.page_no = 0
        await inter.defer()
        row = ActionRow(Button(style=ButtonStyle.blurple, label="◀️", custom_id="prev"),
                        Button(style=ButtonStyle.blurple, label="▶️", custom_id="next"))
        loop = asyncio.get_event_loop()
        user: Member = get(self.client.get_all_members(), id=inter.author.id)
        if title is not None:
            song: Song = await loop.run_in_executor(None, LyricsProcess.fetchlyrics, title, author)
            title, track_url, album_art = song.title, song.url, song.song_art_image_url
        else:        
            for activity in user.activities:
                if isinstance(activity, Spotify):
                    title, author, track_url, album_art = activity.title, activity.artist, activity.track_url, activity.album_cover_url
                    song = await loop.run_in_executor(None, LyricsProcess.fetchlyrics, title, author)

        if isinstance(song, Song) is False: return await inter.edit("Lyrics not Found :(")
        else:
            lyricsList = LyricsProcess.SongTolist(song)
            msg = await inter.edit(embed = LyricsProcess.generate_embed(title=title, track_url=track_url, album_art=album_art, lyricsList=lyricsList, pgno=self.page_no), components = [row])
            on_click = msg.create_click_listener(timeout=360)

            @on_click.matching_id("prev")
            async def on_prev_page(inter: MessageInteraction):
                await inter.acknowledge()
                if self.page_no > 0:
                    self.page_no -= 1
                await msg.edit(embed = LyricsProcess.generate_embed(title=title, track_url=track_url, album_art=album_art, lyricsList=lyricsList, pgno=self.page_no), components = [row])

            @on_click.matching_id("next")
            async def on_next_page(inter: MessageInteraction):
                await inter.acknowledge()
                if self.page_no < len(lyricsList)-1:
                    self.page_no += 1
                await msg.edit(embed = LyricsProcess.generate_embed(title=title, track_url=track_url, album_art=album_art, lyricsList=lyricsList, pgno=self.page_no), components = [row])

            @on_click.timeout
            async def on_timeout():
                await msg.edit(components=[])

def setup(client):
    client.add_cog(Lyrics(client))
