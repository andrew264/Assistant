import asyncio
import re
from typing import Optional

import discord
import wavelink
from discord import app_commands
from discord.ext import commands
from lyricsgenius import Genius
from lyricsgenius.types.song import Song

from assistant import AssistantBot
from config import GENIUS_TOKEN
from utils import remove_brackets

genius = Genius(GENIUS_TOKEN, verbose=False, skip_non_songs=True, timeout=10) if GENIUS_TOKEN else None


class GLyrics:
    def __init__(self):
        self.title: Optional[str] = None
        self.artist: Optional[str] = None
        self.lyrics: Optional[list[str]] = None
        self.url: Optional[str] = None
        self.icon: Optional[str] = None
        self.album_art: Optional[str] = None
        self.colour: Optional[discord.Colour] = None

    @staticmethod
    def _get_lyrics(title, artist) -> Optional[Song]:
        assert genius is not None
        if not title:
            return None
        song: Optional[Song] = genius.search_song(title, artist)
        return song if (song and song.lyrics) else None

    @staticmethod
    def _lyrics_list(lyrics: str) -> list[str]:
        lyrics = lyrics.replace("[", "\n\n[")
        lyrics = re.sub(r"[0-9]*Embed*", "", lyrics)
        lyrics = re.sub(r"URLCopyEmbedCopy", "", lyrics)
        if len(lyrics.splitlines()) > 1 and "lyrics" in lyrics.splitlines()[0].lower():
            lyrics = lyrics.split("\n", 1)[1]
        _lyrics = [lyric for lyric in lyrics.split("\n\n") if lyric.strip() != ""]

        # break up lyrics into chunks of 2048 characters
        lyrics_list = []
        for lyric in _lyrics:
            if len(lyric) > 2048:
                for i in range(0, len(lyric), 2048):
                    lyrics_list.append(lyric[i:i + 2048])
            else:
                lyrics_list.append(lyric)

        return lyrics_list

    def _embeds_list(self) -> list[discord.Embed]:
        embeds = []
        assert self.lyrics is not None
        for i, lines in enumerate(self.lyrics):
            embed = discord.Embed(title=self.title, description=lines, color=self.colour, url=self.url)
            embed.set_thumbnail(url=self.album_art)
            embed.set_footer(text=f"{i + 1}/{len(self.lyrics)}", icon_url=self.icon)
            embeds.append(embed)
        return embeds

    async def get_lyrics(self, author: discord.Member,
                         title: Optional[str] = None, artist: Optional[str] = None,
                         spotify: Optional[discord.Spotify] = None,
                         yt: Optional[wavelink.Playable] = None) -> list[discord.Embed]:
        if not any((title, spotify, yt)):
            return []
        loop = asyncio.get_event_loop()
        if spotify:
            title, artist = remove_brackets(spotify.title), spotify.artists[0]
            self.url = spotify.track_url
            self.icon = "https://open.spotifycdn.com/cdn/images/favicon32.8e66b099.png"
            self.album_art = spotify.album_cover_url
            self.colour = spotify.color
        elif yt:
            if hasattr(yt, "thumbnail"):
                self.album_art = yt.thumbnail
            else:
                self.album_art = None

            # split title into artist and title
            _title = remove_brackets(yt.title).split("-")

            # Title
            title = _title[-1].strip()
            # if 'ft.' in title remove everything after it
            if 'ft.' in title:
                title = title.split('ft.')[0].strip()
            elif 'feat.' in title:
                title = title.split('feat.')[0].strip()

            # Artist
            artist = _title[0].split(',')[0].strip() if len(_title) > 1 else ""
            if '&' in artist:
                artist = artist.split('&')[0].strip()

            self.url = yt.uri
            self.icon = "https://www.gstatic.com/images/branding/product/1x/youtube_64dp.png"
            self.colour = discord.Colour.red()
        else:
            self.icon = author.display_avatar.url
            self.colour = discord.Colour.random()

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
    def __init__(self, bot: AssistantBot):
        self.bot = bot

    @commands.hybrid_command(name="lyrics", description="Get lyrics for a song you are listening to", )
    @app_commands.describe(title='Song Title', artist='Artist Name')
    @commands.guild_only()
    async def lyrics(self, ctx: commands.Context,
                     title: Optional[str] = None,
                     artist: Optional[str] = None) -> None:
        assert ctx.guild
        user = ctx.guild.get_member(ctx.author.id)
        assert user is not None
        await ctx.defer()
        spotify = [act for act in user.activities if isinstance(act, discord.Spotify)]
        embeds = []
        if title:
            embeds = await GLyrics().get_lyrics(user, title, artist)
        elif spotify:
            embeds = await GLyrics().get_lyrics(user, spotify=spotify[0])
        else:
            if ctx.voice_client is not None and user.voice is not None:
                vc: wavelink.Player = ctx.voice_client  # type: ignore
                if vc.channel == user.voice.channel and vc.current:
                    embeds = await GLyrics().get_lyrics(user, yt=vc.current)

        if not embeds:
            await ctx.send(content="Lyrics not found.")
            return
        else:
            class Pages(discord.ui.View):
                def __init__(self):
                    super().__init__(timeout=120.0)
                    self.page_no = 0
                    self.message: Optional[discord.Message] = None

                async def on_timeout(self):
                    self.stop()
                    await self.message.edit(view=None)

                @discord.ui.button(emoji="◀", style=discord.ButtonStyle.blurple)
                async def prev_page(self, interaction: discord.Interaction, button: discord.Button) -> None:
                    if self.page_no > 0:
                        self.page_no -= 1
                    else:
                        self.page_no = len(embeds) - 1
                    await interaction.response.edit_message(embed=embeds[self.page_no], view=self, )

                @discord.ui.button(emoji="▶", style=discord.ButtonStyle.blurple)
                async def next_page(self, interaction: discord.Interaction, button: discord.Button) -> None:
                    if self.page_no < len(embeds) - 1:
                        self.page_no += 1
                    else:
                        self.page_no = 0
                    await interaction.response.edit_message(embed=embeds[self.page_no], view=self, )

                @discord.ui.button(emoji="❌", style=discord.ButtonStyle.gray)
                async def remove_buttons(self, interaction: discord.Interaction, button: discord.Button) -> None:
                    await interaction.response.edit_message(view=None)
                    self.stop()

            view = Pages()
            view.message = await ctx.send(embed=embeds[0], view=view)


async def setup(bot: AssistantBot):
    if not GENIUS_TOKEN:
        bot.logger.warning("Genius Token not found. Lyrics command will not be loaded.")
        return
    await bot.add_cog(Lyrics(bot))
