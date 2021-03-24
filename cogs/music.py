import discord
from discord.ext import commands
from discord.utils import get
import youtube_dl
import os

class music(commands.Cog):
    def __init__(self,client):
        self.client = client

    @commands.command(pass_context=True, brief="This will play a song .play [url]", aliases=['p'])
    async def play(self, ctx, url:str=''):
        print(f'Youtube Link: {url}')
        song_there = os.path.isfile("song.mp3")
        try:
            if song_there:
                os.remove("song.mp3")
        except PermissionError:
            if ctx.voice_client.is_paused() is True:
                return await ctx.voice_client.resume()
            else:
                return await ctx.send("Wait for the current playing music to end or use the '.stop' command")
        print(f'Connecting to {ctx.message.author.voice.channel}')
        voiceChannel = ctx.message.author.voice.channel
        if not voiceChannel:
            await ctx.send("You are not connected to a voice channel.")
            return
        voice = get(self.client.voice_clients, guild=ctx.guild)

        if voice and voice.is_connected():
            await voice.move_to(voiceChannel)
        else:
            voice = await voiceChannel.connect()

        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        if url == '':
            return await ctx.send('Provide a Youtube URL to play.')
        reply = await ctx.send('Loading...')
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        for file in os.listdir("./"):
            if file.endswith(".mp3"):
                yt_title = file
                os.rename(file, "song.mp3")
        voice.play(discord.FFmpegPCMAudio("song.mp3"))
        await reply.edit(content=f'Playing: {yt_title[:-16]}')


    @commands.has_permissions(manage_channels=True)
    @commands.command()
    async def stop(self, ctx):
        if ctx.message.author.voice is None:
            return await ctx.send('You must be is same VC as the bot.')
        if ctx.voice_client is None:
            return await ctx.send('Bot is not connect to a VC.')
        if ctx.message.author.voice is not None and ctx.voice_client is not None:
            if ctx.voice_client.is_playing() is True or ctx.voice_client.is_paused() is True or ctx.voice_client is not None:
                ctx.voice_client.stop()
                return await ctx.send('Stopped.') ,await ctx.voice_client.disconnect()
            return await ctx.send('No audio is being played.')

    @commands.command()
    async def pause(self, ctx):
        if ctx.message.author.voice is None:
            return await ctx.send('You must be is same VC as the bot.')
        if ctx.voice_client is None:
            return await ctx.send('Bot is not connect to a VC.')
        if ctx.message.author.voice is not None and ctx.voice_client is not None:
            if ctx.voice_client.is_paused() is False:
                ctx.voice_client.pause()
                return await ctx.send('Paused.')

def setup(client):
	client.add_cog(music(client))
