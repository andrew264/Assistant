# Imports
import os

import yt_dlp.YoutubeDL as YDL
from disnake import Client, ApplicationCommandInteraction, Embed, File
from disnake.ext import commands
from disnake.ext.commands import Param

ydl_opts = {
    'format': 'bestvideo[height<=240]+bestaudio/best[height<=240]',
    'videoformat': "mp4",
    'outtmpl': './downloads/%(title)s.%(ext)s',
    'quiet': True,
    'postprocessors': [{
        'key': 'FFmpegVideoConvertor',
        'preferedformat': 'mp4',
    }],
}


class VidDownload(commands.Cog):
    def __init__(self, client: Client):
        self.client = client

    @commands.slash_command(name="videodownloader", description="Get Video Sent in Chat")
    async def VDownloader(self, inter: ApplicationCommandInteraction,
                          url: str = Param(description="Video URL", default=None)) -> None:
        await inter.response.defer(ephemeral=True)
        with YDL(ydl_opts) as ydl:
            video_info = ydl.extract_info(url, download=True)
        embed = Embed(title=video_info['title'], url=video_info['webpage_url'], color=0x4F91F6)
        embed.set_thumbnail(url=video_info['thumbnails'][-1]['url'])
        embed.set_footer(text=f"From {video_info['extractor'].capitalize()}", icon_url=inter.author.display_avatar.url)
        await inter.edit_original_message(embed=embed)
        for file in os.listdir("./downloads"):
            if file.endswith(".mp4"):
                print()
                if os.path.getsize(f"./downloads/{file}") <= 8388608:
                    await inter.channel.send(file=File(f"./downloads/{file}"))
                else:
                    await inter.channel.send(
                        f"{video_info['title']}\n" +
                        f"File to Large({(os.path.getsize(f'./downloads/{file}'))/1024} KB) to send\n" +
                        f"{video_info['formats'][-1]['url']}")
                os.remove(f"./downloads/{file}")


def setup(client):
    client.add_cog(VidDownload(client))
