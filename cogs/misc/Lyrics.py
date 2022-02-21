# Imports
import asyncio
import re
from typing import Optional

import disnake
import yt_dlp.YoutubeDL as YDL
from disnake.ext import commands
from disnake.ext.commands import Param
from lavalink import DefaultPlayer as Player
from lyricsgenius import Genius
from lyricsgenius.types import Song

import assistant
from EnvVariables import GENIUS_TOKEN

ydl_opts = {'quiet': True, 'no_warnings': True}
genius = Genius(GENIUS_TOKEN, verbose=False)


def fetch_lyrics(song_title: str, artist_name: str = "") -> Optional[Song]:
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

    def generate_embed(self, pg_no: int, ) -> disnake.Embed:
        embed = disnake.Embed(title=f"{self.title}", url=self.track_url,
                              color=0x1DB954, description=self.lyrics_list[pg_no])
        embed.set_thumbnail(url=self.album_art)
        embed.set_footer(text=f"({pg_no + 1}/{len(self.lyrics_list)})", icon_url=self.avatar_url)
        return embed


class Pages(disnake.ui.View):
    def __init__(self, song_info: SongInfo, inter: disnake.ApplicationCommandInteraction):
        super().__init__(timeout=120.0)
        self.page_no = 0
        self.song_info = song_info
        self.inter = inter

    async def on_timeout(self):
        try:
            await self.inter.edit_original_message(view=None)
        except disnake.NotFound | disnake.Forbidden:
            pass

    @disnake.ui.button(emoji="◀", style=disnake.ButtonStyle.blurple)
    async def prev_page(self, button: disnake.Button, interaction: disnake.Interaction) -> None:
        if self.page_no > 0:
            self.page_no -= 1
        else:
            self.page_no = len(self.song_info.lyrics_list) - 1
        await interaction.response.edit_message(embed=self.song_info.generate_embed(self.page_no), view=self, )

    @disnake.ui.button(emoji="▶", style=disnake.ButtonStyle.blurple)
    async def next_page(self, button: disnake.Button, interaction: disnake.Interaction) -> None:
        if self.page_no < len(self.song_info.lyrics_list) - 1:
            self.page_no += 1
        else:
            self.page_no = 0
        await interaction.response.edit_message(embed=self.song_info.generate_embed(self.page_no), view=self, )


class Lyrics(commands.Cog):
    def __init__(self, client: assistant.Client):
        self.client = client

    @commands.slash_command(description="Get Lyrics for the song you are currently listening to.")
    async def lyrics(self, inter: disnake.ApplicationCommandInteraction,
                     title: str = Param(description="Song Title", default=None),
                     artist: str = Param(description="Song Artist", default=""), ) -> None:

        await inter.response.defer()
        spotify = False
        track_url: Optional[str] = None
        icon_url: Optional[str] = inter.author.display_avatar.url

        if not title and not isinstance(inter.author, disnake.Member):
            await inter.edit_original_message(content="Please provide a song title.")
            return

        # fetch title from Spotify Activity
        if not title:
            for activity in inter.author.activities:
                if isinstance(activity, disnake.Spotify):
                    title = activity.title
                    artist = activity.artist
                    track_url = activity.track_url
                    spotify = True
                    icon_url = "https://open.scdn.co/cdn/images/favicon32.8e66b099.png"
                    break

        # fetch title from currently playing song
        if not spotify and not title:
            if inter.me.voice is not None and inter.author.voice is not None:
                if inter.me.voice.channel == inter.author.voice.channel:
                    player: Player = self.client.lavalink.player_manager.get(inter.guild.id)
                    if player and player.current:
                        with YDL(ydl_opts) as ydl:
                            video = ydl.extract_info(f'{player.current.identifier}', download=False)
                        try:
                            title = re.sub(r"\([^()]*\)", "", video["track"])
                            artist = list((video["artist"]).split(","))[0]
                        except KeyError:
                            pass
                        track_url = player.current.uri
                        icon_url = inter.bot.user.display_avatar.url

        loop = asyncio.get_event_loop()
        if title:
            song = await loop.run_in_executor(None, fetch_lyrics, title, artist)
            if isinstance(song, Song) and hasattr(song, "url") and track_url:
                song.url = track_url
        else:
            await inter.edit_original_message(content="Please provide a song title.")
            return

        if song is None:
            await inter.edit_original_message(content="Lyrics not Found :(")
            return

        song_info: SongInfo = SongInfo(song, icon_url, )
        my_pages = Pages(song_info, inter)
        await inter.edit_original_message(embed=song_info.generate_embed(0), view=my_pages, )


def setup(client):
    client.add_cog(Lyrics(client))
