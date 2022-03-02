import asyncio
import re
from typing import Optional

import disnake
from disnake.ext import commands
from lavalink.client import DefaultPlayer as Player
from lyricsgenius import Genius
from lyricsgenius.song import Song
from yt_dlp import YoutubeDL

from EnvVariables import GENIUS_TOKEN
from assistant import Client, VideoTrack, remove_brackets, colour_gen

genius = Genius(GENIUS_TOKEN, verbose=False, skip_non_songs=True, )
ydl_opts = {'quiet': True, 'no_warnings': True, }


class GLyrics:
    def __init__(self):
        self.title: Optional[str] = None
        self.artist: Optional[str] = None
        self.lyrics: Optional[list[str]] = None
        self.url: Optional[str] = None
        self.icon: Optional[str] = None
        self.album_art: Optional[str] = None
        self.colour: Optional[int] = None

    @staticmethod
    def _get_lyrics(title, artist) -> Optional[Song]:
        song: Song = genius.search_song(title, artist)
        return song if (song and song.lyrics) else None

    @staticmethod
    def _lyrics_list(lyrics) -> list[str]:
        lyrics = re.sub(r"[0-9]*Embed*", "", lyrics)
        lyrics = re.sub(r"URLCopyEmbedCopy", "", lyrics)
        return list(lyrics.split("\n\n"))

    @staticmethod
    def _get_from_yt(identifier):
        with YoutubeDL(ydl_opts) as ydl:
            video = ydl.extract_info(identifier, download=False)
        try:
            title: str = re.sub(r"\([^()]*\)", "", video["track"])
            artist: str = list((video["artist"]).split(","))[0]
        except KeyError:
            return None
        return title, artist

    def _embeds_list(self) -> list[disnake.Embed]:
        embeds = []
        for i, lines in enumerate(self.lyrics):
            embed = disnake.Embed(title=self.title, description=lines, color=self.colour, url=self.url)
            embed.set_thumbnail(url=self.album_art)
            embed.set_footer(text=f"{i + 1}/{len(self.lyrics)}", icon_url=self.icon)
            embeds.append(embed)
        return embeds

    async def get_lyrics(self, author: disnake.Member,
                         title: Optional[str] = None, artist: Optional[str] = None,
                         spotify: Optional[disnake.Spotify] = None,
                         yt: Optional[VideoTrack] = None) -> list[disnake.Embed]:
        if not any((title, spotify, yt)):
            return []
        loop = asyncio.get_event_loop()
        if spotify:
            title, artist = remove_brackets(spotify.title), spotify.artists[0]
            self.url = spotify.track_url
            self.icon = "https://open.scdn.co/cdn/images/favicon32.8e66b099.png"
            self.album_art = spotify.album_cover_url
            self.colour = spotify.color
        elif yt:
            title, artist = await loop.run_in_executor(None, self._get_from_yt, yt.identifier)
            self.url = yt.uri
            self.icon = "https://www.gstatic.com/images/branding/product/1x/youtube_64dp.png"
            self.album_art = yt.thumbnail
            self.colour = 0xFF0000
        else:
            self.icon = author.display_avatar.url
            self.colour = colour_gen(author.id, as_hex=True)

        song: Optional[Song] = await loop.run_in_executor(None, self._get_lyrics, title, artist)
        if song is None:
            return []
        self.title = song.title
        self.artist = song.artist
        self.lyrics = self._lyrics_list(song.lyrics)
        self.url = self.url if self.url else song.url
        self.album_art = self.album_art if self.album_art else song.song_art_image_url
        return self._embeds_list()


class Lyrics(commands.Cog):
    def __init__(self, client: Client):
        self.client = client

    @commands.slash_command(name="lyrics", description="Get lyrics for a song you are listening to", )
    async def lyrics(self, inter: disnake.ApplicationCommandInteraction,
                     title: str = commands.Param(description="Song Title", default=None),
                     artist: str = commands.Param(description="Song Artist", default=""), ) -> None:
        await inter.response.defer()
        spotify = [act for act in inter.author.activities if isinstance(act, disnake.Spotify)]
        embeds = []
        if title:
            embeds = await GLyrics().get_lyrics(inter.author, title, artist)
        elif spotify:
            embeds = await GLyrics().get_lyrics(inter.author, spotify=spotify[0])
        else:
            if inter.me.voice is not None and inter.author.voice is not None:
                if inter.me.voice.channel == inter.author.voice.channel:
                    player: Player = self.client.lavalink.player_manager.get(inter.guild.id)
                    if player and player.current:
                        embeds = await GLyrics().get_lyrics(inter.author, yt=player.current)

        if not embeds:
            await inter.edit_original_message(content="Lyrics not found.")
            return
        else:
            class Pages(disnake.ui.View):
                def __init__(self):
                    super().__init__(timeout=120.0)
                    self.page_no = 0

                async def on_timeout(self):
                    try:
                        await inter.edit_original_message(view=None)
                    except disnake.NotFound | disnake.Forbidden:
                        pass

                @disnake.ui.button(emoji="◀", style=disnake.ButtonStyle.blurple)
                async def prev_page(self, button: disnake.Button, interaction: disnake.Interaction) -> None:
                    if self.page_no > 0:
                        self.page_no -= 1
                    else:
                        self.page_no = len(embeds) - 1
                    await interaction.response.edit_message(embed=embeds[self.page_no], view=self, )

                @disnake.ui.button(emoji="▶", style=disnake.ButtonStyle.blurple)
                async def next_page(self, button: disnake.Button, interaction: disnake.Interaction) -> None:
                    if self.page_no < len(embeds) - 1:
                        self.page_no += 1
                    else:
                        self.page_no = 0
                    await interaction.response.edit_message(embed=embeds[self.page_no], view=self, )

            await inter.edit_original_message(embed=embeds[0], view=Pages())


def setup(client):
    client.add_cog(Lyrics(client))
