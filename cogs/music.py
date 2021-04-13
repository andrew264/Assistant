from discord.ext import commands, tasks
from discord.utils import get
from discord import FFmpegPCMAudio, Activity, ActivityType, Status
from olmusic import check_urls
import youtube_dl.YoutubeDL as YDL
ydl_opts = {
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'format': 'bestaudio/best',
}
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
song_title=''

class music(commands.Cog):
    def __init__(self,client):
        self.client = client

    @commands.command(pass_context=True, brief='This will play a song .play [url]', aliases=['p'])
    async def play(self, ctx,*,url:str=''):
        global song_title
        
        # Check if author in VC
        if ctx.author.voice is None or ctx.author.voice.channel is None:
            return await ctx.send("You are not connected to a voice channel.")
        # Check da url for bad stuff
        if check_urls(url):
            return await ctx.send('Thats not a fucking song.')
        # If player is_paused resume...
        if url=='' and ctx.voice_client.is_paused() is True:
            await ctx.send(f'Resuming: `{song_title}`')
            music.status_set.start(self, ctx)
            return await ctx.voice_client.resume()
        # Join/Move to vc
        voice = get(self.client.voice_clients, guild=ctx.guild)
        voiceChannel = ctx.message.author.voice.channel
        if voice and voice.is_connected():
            await voice.move_to(voiceChannel)
        else:
            voice = await voiceChannel.connect()
        # If is_playing gtfo
        if voice and voice.is_playing() is True:
            return await ctx.send('Wait for the current playing music to end or use the \'.stop\' command')
  
        print(f'Connecting to {ctx.message.author.voice.channel}')
        reply = await ctx.send('Loading...')
        with YDL(ydl_opts) as ydl:
            try:
                song_info = ydl.extract_info(url, download=False)
            except:
                song_info = ydl.extract_info(f'ytsearch:{url}', download=False)['entries'][0]
            songurl=song_info["formats"][0]["url"]
            song_title = song_info.get('title', None)
        voice.play(FFmpegPCMAudio(songurl, **FFMPEG_OPTIONS))
        await reply.edit(content=f'Playing: `{song_title}`')
        music.status_set.start(self, ctx)
            
    @tasks.loop(seconds = 5)
    async def status_set(self, ctx):
        if ctx.voice_client is not None and ctx.voice_client.is_playing() and song_title:
            await self.client.change_presence(activity=Activity(type=ActivityType.listening, name=f"{song_title}"))
        else:
            await self.client.change_presence(status=Status.idle, activity=Activity(type=ActivityType.watching, name="my Homies."))
            music.status_set.cancel()

    @commands.has_permissions(manage_channels=True)
    @commands.command()
    async def stop(self, ctx):
        if ctx.message.author.voice is None:
            return await ctx.send('You must be is same VC as the bot.')
        if ctx.voice_client is None:
            return await ctx.send('Bot is not connect to VC.')
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
            return await ctx.send('Bot is not connect to VC.')
        if ctx.message.author.voice is not None and ctx.voice_client is not None:
            if ctx.voice_client.is_paused() is False:
                ctx.voice_client.pause()
                return await ctx.send(f'Paused: `{song_title}`')

def setup(client):
	client.add_cog(music(client))
