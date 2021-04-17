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

    #Play
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
            embed=Embed(title='Resumed:',colour=0x4169e1)
            embed.add_field(name=song_title_list[0],value='\u200b')
            await ctx.send(embed=embed)
            music.status_set.start(self, ctx)
            return ctx.voice_client.resume()

        #find vid url and add to list
        with YDL(ydl_opts) as ydl:
            try:
                song_info = ydl.extract_info(url, download=False)
            except:
                song_info = ydl.extract_info(f'ytsearch:{url}', download=False)['entries'][0]
            song_list.append(song_info.get("webpage_url"))
            song_title = song_info.get('title', None)
            song_title_list.append(song_title)
            await ctx.send(f'Adding {song_title} to Queue.')
            if music.play_from_queue.is_running() is False:
                music.play_from_queue.start(self, ctx)

    #Status Update
    @tasks.loop(seconds = 5)
    async def status_set(self, ctx):
        if ctx.voice_client is not None and ctx.voice_client.is_playing() and song_title:
            await self.client.change_presence(activity=Activity(type=ActivityType.listening, name=f"{song_title}"))
        else:
            await self.client.change_presence(status=Status.idle, activity=Activity(type=ActivityType.watching, name="my Homies."))
            music.status_set.cancel()

    #Queue
    @commands.command(aliases=['q'])
    async def queue(self, ctx):
        if len(song_title_list)==0:
            await ctx.send('Queue is Empty.')
        else:
            embed=Embed(title="Songs in Queue",colour=0xffa31a)
            embed.add_field(name='Now Playing',value=f'{song_title_list[0]}', inline=False)
            if len(song_title_list)>1:
                embed.add_field(name='Next in Queue',value=f'1. {song_title_list[1]}', inline=False)
                for i in range(2,len(song_title_list)):
                    embed.add_field(name='\u200b',value=f'{i}. {song_title_list[i]}', inline=False)
            await ctx.send(embed=embed)

    #Play from Queue
    @tasks.loop(seconds = 1)
    async def play_from_queue(self, ctx):
        global song_list, song_title, song_title_list, duration
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
            voice.play(FFmpegPCMAudio(song_url, **FFMPEG_OPTIONS))
            # counting down song duration 
            while duration>1:
                await asyncio.sleep(1)
                duration=duration-1
            # pop [0] from lists
            if song_list:
                song_list.pop(0)
                song_title_list.pop(0)
            
        else: 
            music.play_from_queue.cancel()

    #Skip
    @commands.command()
    async def skip(self, ctx, arg=0):
        global song_list, song_title_list, duration
        if ctx.message.author.voice is None:
            return await ctx.send('You must be is same VC as the bot.')
        if ctx.voice_client is None:
            return await ctx.send('Bot is not connect to VC.')
        if ctx.message.author.voice is not None and ctx.voice_client is not None:
            if ctx.voice_client.is_playing() is True or ctx.voice_client.is_paused() is True or ctx.voice_client is not None:
                embed=Embed(title='Removed',colour=0xff7f50)
                if arg>0 and arg<len(song_list):
                    embed.add_field(name=f'{song_title_list[arg]} from Queue.',value='\u200b')
                    await ctx.send(embed=embed)
                    song_list.pop(arg)
                    song_title_list.pop(arg)
                elif arg==0:
                    if len(song_title_list):
                        embed.add_field(name=f'{song_title_list[arg]} from Queue.',value='\u200b')
                        ctx.voice_client.stop()
                        duration = 1
                        await ctx.send(embed=embed)
                    else:
                        embed.add_field(name='Nothing',value=':p')
                        await ctx.send(embed=embed)
        else: await ctx.send('Queue is Empty')

    #Stop
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
                if music.play_from_queue.is_running() is True:
                    music.play_from_queue.cancel()
                return await ctx.message.add_reaction('👋') ,await ctx.voice_client.disconnect()
            return await ctx.send('No audio is being played.')

    #Pause
    @commands.command()
    async def pause(self, ctx):
        if ctx.message.author.voice is None:
            return await ctx.send('You must be is same VC as the bot.')
        if ctx.voice_client is None:
            return await ctx.send('Bot is not connect to VC.')
        if ctx.message.author.voice is not None and ctx.voice_client is not None:
            if ctx.voice_client.is_paused() is False:
                ctx.voice_client.pause()
                embed=Embed(title='Paused:',colour=0x4169e1)
                embed.add_field(name=song_title,value='\u200b')
                await ctx.send(embed=embed)
                # we addin 1 every second to wait :p
                global duration
                while ctx.voice_client.is_paused():
                    duration=duration+1
                    await asyncio.sleep(1)

def setup(client):
	client.add_cog(music(client))
