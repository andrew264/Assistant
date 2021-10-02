from discord.ext import commands
from olenv import GENIUS_TOKEN
from discord import Spotify, Embed, Member
from discord.utils import get
import lyricsgenius
import re
from dislash import ActionRow, Button, ButtonStyle
from dislash.interactions.app_command_interaction import SlashInteraction
from dislash.interactions import MessageInteraction
from dislash.application_commands import slash_client
import asyncio

genius = lyricsgenius.Genius(GENIUS_TOKEN, verbose=False)

class LyricsProcess():

    def __init__(self):
        pass

    def strTolist(lyrics:str):
        lyrics = re.sub(r"[0-9]*URLCopyEmbedCopy",'',lyrics)
        lyricsList = list(lyrics.split("\n\n"))
        return lyricsList

    def fetchsong(activity: Spotify):
        lyrics:str = None
        song_title = re.sub(r'\([^()]*\)', '', activity.title)
        artist_name = activity.artists[0]
        song = genius.search_song(song_title, artist_name)
        if song is not None and song.lyrics is not None:
            lyrics = song.lyrics
        return lyrics

    def generate_embed(activity: Spotify, lyricsList: list, pgno:int):
        embed = Embed(title = f'{activity.title} ({pgno+1}/{len(lyricsList)})', url= activity.track_url, color=0x1DB954, description=lyricsList[pgno])
        embed.set_thumbnail(url = activity.album_cover_url)
        return embed

class Lyrics(commands.Cog):

    def __init__(self,client):
        self.client = client
      
    @slash_client.slash_command(description="Get Lyrics for the song you are currently listening to.")
    async def lyrics(self, inter: SlashInteraction):
        self.page_no = 0
        spotActivity = None
        await inter.defer()
        user: Member = get(self.client.get_all_members(), id=inter.author.id)
        row = ActionRow(Button(style=ButtonStyle.blurple, label="◀️", custom_id="prev"),
                        Button(style=ButtonStyle.blurple, label="▶️", custom_id="next"))
        for activity in user.activities:
            if isinstance(activity, Spotify):
                spotActivity: Spotify = activity
        if spotActivity is not None:
            loop = asyncio.get_event_loop()
            lyrics = await loop.run_in_executor(None, LyricsProcess.fetchsong, spotActivity)
        else: return await inter.edit("Listen to a song in Spotify to get Lyrics.", ephemeral=True)
        if lyrics is not None:
            lyricsList = LyricsProcess.strTolist(lyrics)
            msg = await inter.edit(embed = LyricsProcess.generate_embed(spotActivity, lyricsList, self.page_no), components = [row])
            on_click = msg.create_click_listener(timeout=360)

            @on_click.matching_id("prev")
            async def on_prev_page(inter: MessageInteraction):
                await inter.acknowledge()
                if self.page_no > 0:
                    self.page_no -= 1
                await msg.edit(embed = LyricsProcess.generate_embed(spotActivity, lyricsList, self.page_no), components = [row])

            @on_click.matching_id("next")
            async def on_next_page(inter: MessageInteraction):
                await inter.acknowledge()
                if self.page_no < len(lyricsList)-1:
                    self.page_no += 1
                await msg.edit(embed = LyricsProcess.generate_embed(spotActivity, lyricsList, self.page_no), components = [row])

            @on_click.timeout
            async def on_timeout():
                await msg.edit(components=[])

        else: return await inter.send("Lyrics not Found :(", ephemeral=True)

def setup(client):
    client.add_cog(Lyrics(client))
