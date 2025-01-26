import asyncio
import re
from dataclasses import dataclass
from typing import Optional, Tuple

import discord
import wavelink
from cachetools import TTLCache
from discord import app_commands
from discord.ext import commands
from lyricsgenius import Genius
from lyricsgenius.types.song import Song

from assistant import AssistantBot
from config import GENIUS_TOKEN
from utils import remove_brackets

genius = None
if GENIUS_TOKEN:
    genius = Genius(GENIUS_TOKEN, verbose=False, skip_non_songs=True, timeout=15)
    genius.remove_section_headers = True

lyrics_cache = TTLCache(maxsize=200, ttl=7200)


@dataclass
class LyricsData:
    title: Optional[str] = None
    artist: Optional[str] = None
    lyrics: Optional[list[str]] = None
    url: Optional[str] = None
    icon: Optional[str] = None
    album_art: Optional[str] = None
    color: Optional[discord.Color] = None


class LyricsManager:
    @staticmethod
    def _get_cache_key(title: str, artist: Optional[str]) -> Tuple[str, Optional[str]]:
        return title.lower(), artist.lower() if artist else None

    @staticmethod
    def _search_genius(title: str, artist: Optional[str]) -> Optional[Song]:
        """Search for lyrics using Genius API"""
        if not genius or not title:
            return None

        cache_key = LyricsManager._get_cache_key(title, artist)
        if cache_key in lyrics_cache:
            return lyrics_cache[cache_key]

        try:
            song = genius.search_song(title, artist)
            if song and song.lyrics:
                lyrics_cache[cache_key] = song
                return song
        except Exception as e:
            print(f"Genius API error: {e}")
        return None

    @staticmethod
    def _process_lyrics(raw_lyrics: str) -> list[str]:
        """Process raw lyrics into formatted chunks"""
        cleaned = re.sub(r"(URLCopyEmbedCopy|You might also like|\d*Embed)|\[.*?\]", "", raw_lyrics)

        if len(cleaned.splitlines()) > 1 and "lyrics" in cleaned.splitlines()[0].lower():
            cleaned = cleaned.split("\n", 1)[1]

        sections = [s.strip() for s in cleaned.split("\n\n") if s.strip()]
        chunks = []
        for section in sections:
            while len(section) > 2048:
                split_pos = section.rfind('\n', 0, 2048)
                if split_pos == -1:
                    split_pos = 2048
                chunks.append(section[:split_pos])
                section = section[split_pos:]
            chunks.append(section)
        return chunks

    @classmethod
    async def fetch_lyrics(cls, *, title: Optional[str] = None, artist: Optional[str] = None, spotify: Optional[discord.Spotify] = None,
                           track: Optional[wavelink.Playable] = None) -> Optional[LyricsData]:
        """Fetch lyrics from various sources"""
        data = LyricsData()

        if spotify:
            data.title = remove_brackets(spotify.title)
            data.artist = spotify.artists[0]
            data.url = spotify.track_url
            data.icon = "https://open.spotifycdn.com/cdn/images/favicon32.8e66b099.png"
            data.album_art = spotify.album_cover_url
            data.color = spotify.color
        elif track:
            data.title = remove_brackets(track.title)
            data.artist = track.author
            data.url = track.uri
            data.album_art = track.thumbnail if hasattr(track, "thumbnail") else None
            data.icon = "https://www.gstatic.com/images/branding/product/1x/youtube_64dp.png"
            data.color = discord.Color.red()
        elif title:
            data.title = title
            data.artist = artist
            data.color = discord.Color.random()
        else:
            return None

        loop = asyncio.get_event_loop()
        song = await loop.run_in_executor(None, cls._search_genius, data.title, data.artist)
        if not song or not song.lyrics:
            return None

        data.lyrics = cls._process_lyrics(song.lyrics)
        data.url = data.url or song.url
        data.album_art = data.album_art or song.song_art_image_url
        return data


class LyricsView(discord.ui.View):
    def __init__(self, embeds: list[discord.Embed]):
        super().__init__(timeout=120)
        self.embeds = embeds
        self.page = 0
        self._update_buttons()

    def _update_buttons(self):
        self.prev_button.disabled = self.page == 0
        self.next_button.disabled = self.page == len(self.embeds) - 1

    @discord.ui.button(emoji="◀", style=discord.ButtonStyle.blurple)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = max(0, self.page - 1)
        self._update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.page], view=self)

    @discord.ui.button(emoji="▶", style=discord.ButtonStyle.blurple)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = min(len(self.embeds) - 1, self.page + 1)
        self._update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.page], view=self)

    @discord.ui.button(emoji="❌", style=discord.ButtonStyle.grey)
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await interaction.delete_original_response()
        self.stop()


class LyricsCog(commands.Cog):
    def __init__(self, bot: AssistantBot):
        self.bot = bot

    @commands.hybrid_command(name="lyrics", description="Get lyrics for the current song or specified track")
    @app_commands.describe(title="Song title", artist="Artist name")
    @commands.guild_only()
    async def lyrics_command(self, ctx: commands.Context, title: Optional[str] = None, artist: Optional[str] = None) -> None:
        """Get lyrics for the current playing song or specified track"""
        await ctx.defer()

        user = ctx.guild.get_member(ctx.author.id)
        spotify = next((act for act in user.activities if isinstance(act, discord.Spotify)), None)
        track = None
        if ctx.voice_client and user.voice and ctx.voice_client.channel == user.voice.channel:
            track = ctx.voice_client.current

        data = await LyricsManager.fetch_lyrics(title=title, artist=artist, spotify=spotify, track=track)

        if not data or not data.lyrics:
            await ctx.send("❌ Couldn't find lyrics for this track", delete_after=15)
            return

        embeds = []
        for i, chunk in enumerate(data.lyrics):
            embed = discord.Embed(title=data.title, description=chunk, color=data.color, url=data.url)
            embed.set_thumbnail(url=data.album_art)
            embed.set_footer(text=f"Lyrics provided by Genius • Page {i + 1}/{len(data.lyrics)}", icon_url=data.icon)
            embeds.append(embed)

        view = LyricsView(embeds) if len(embeds) > 1 else None
        await ctx.send(embed=embeds[0], view=view)


async def setup(bot: AssistantBot):
    if not GENIUS_TOKEN:
        bot.logger.warning("Genius token not found - lyrics command disabled")
        return
    await bot.add_cog(LyricsCog(bot))
