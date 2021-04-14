from discord.ext import commands, tasks
from discord.utils import get
from discord import FFmpegPCMAudio, Activity, ActivityType, Status, Embed
from olmusic import check_urls
import time
import asyncio
import youtube_dl.YoutubeDL as YDL
ydl_opts = {
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'format': 'bestaudio/best',
}
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
song_title=''
song_list=[]
song_title_list=[]

class music(commands.Cog):
    def __init__(self,client):
        self.client = client

    @commands.command(pass_context=True, brief='This will play a song .play [url]', aliases=['p','P'])
    async def play(self, ctx,*,url:str=''):
        global song_list, song_title_list
        
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

        #find vid url and add to list
        with YDL(ydl_opts) as ydl:
            try:
                song_info = ydl.extract_info(url, download=False)
            except:
                song_info = ydl.extract_info(f'ytsearch:{url}', download=False)['entries'][0]
            song_list.append(song_info.get("webpage_url"))
            song_title = song_info.get('title', None)
            song_title_list.append(song_title)
            print(song_title_list)
            await ctx.send(f'Adding {song_title} to Queue.')
            if music.play_from_queue.is_running() is False:
                music.play_from_queue.start(self, ctx)

    @tasks.loop(seconds = 5)
    async def status_set(self, ctx):
        if ctx.voice_client is not None and ctx.voice_client.is_playing() and song_title:
            await self.client.change_presence(activity=Activity(type=ActivityType.listening, name=f"{song_title}"))
        else:
            await self.client.change_presence(status=Status.idle, activity=Activity(type=ActivityType.watching, name="my Homies."))
            music.status_set.cancel()

    @commands.command(aliases=['q'])
    async def queue(self, ctx):
        await ctx.send(song_title_list)

    @tasks.loop(seconds = 1)
    async def play_from_queue(self, ctx):
        global song_list, song_title, song_title_list
        # Join VC
        voice = get(self.client.voice_clients, guild=ctx.guild)
        voiceChannel = ctx.message.author.voice.channel
        if voice == None:
            voice = await voiceChannel.connect()
        # Begin search
        if song_list:
            with YDL(ydl_opts) as ydl:
                song_info = ydl.extract_info(song_list[0], download=False)
                song_url=song_info["formats"][0]["url"]
                song_title = song_info.get('title', None)
                song_thumbnail = song_info.get("thumbnail")
                song_webpage = song_info.get("webpage_url")
                song_rating = round(song_info.get("average_rating"),2)
                # in mm:ss
                song_length = time.strftime('%M:%S', time.gmtime(song_info.get("duration")))
                # in sec
                duration = song_info.get("duration")
            voice.play(FFmpegPCMAudio(song_url, **FFMPEG_OPTIONS))
            # Embed
            embed=Embed(title="", color=0xff0000)
            embed.set_thumbnail(url=f'{song_thumbnail}')
            embed.set_author(name=f'Playing: {song_title}', url=song_webpage, icon_url='')
            embed.add_field(name="Duration:", value=song_length, inline=True)
            embed.add_field(name="Requested by:", value=ctx.message.author.display_name, inline=True)
            embed.add_field(name="Song Rating:", value=f'{song_rating}/5', inline=True)
            await ctx.send(embed=embed)
            if music.status_set.is_running() is False:
                music.status_set.start(self, ctx)
            await asyncio.sleep(duration)
            song_list.pop(0)
            song_title_list.pop(0)
        else: 
            music.play_from_queue.cancel()


    @commands.command(aliases=['dc'])
    async def stop(self, ctx):
        global song_list, song_title_list
        if ctx.message.author.voice is None:
            return await ctx.send('You must be is same VC as the bot.')
        if ctx.voice_client is None:
            return await ctx.send('Bot is not connect to VC.')
        if ctx.message.author.voice is not None and ctx.voice_client is not None:
            if ctx.voice_client.is_playing() is True or ctx.voice_client.is_paused() is True or ctx.voice_client is not None:
                ctx.voice_client.stop()
                song_list.clear()
                song_title_list.clear()
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
