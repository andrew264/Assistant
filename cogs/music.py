from discord.ext import commands, tasks
from discord.utils import get
from discord import FFmpegPCMAudio, PCMVolumeTransformer, Activity, ActivityType, Status, Embed
import time
from datetime import datetime
import asyncio
import youtube_dl.YoutubeDL as YDL
ydl_opts = {
    'quiet': True,
    'no_warnings': True,
    'format': 'bestaudio/best',
}
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

def human_format(num):
    num = float('{:.3g}'.format(num))
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])

class video_info:
    def __init__(self, link: str):
        with YDL(ydl_opts) as ydl:
            YT_extract = ydl.extract_info(link, download=False)
            self.Title:str = (YT_extract.get("title", None))
            self.pURL:str = (YT_extract.get("webpage_url"))
            self.URL:str = (YT_extract["formats"][0]["url"])
            self.Thumbnail:str = (YT_extract.get("thumbnail"))
            self.Rating:float = (round(YT_extract.get("average_rating"),2))
            self.Views:int = (YT_extract.get("view_count"))
            self.Likes:int = (YT_extract.get("like_count"))
            self.UploadDate:str = (datetime.strptime(YT_extract.get('upload_date'), '%Y%m%d').strftime('%d-%m-%Y'))
            self.Duration:int = (YT_extract.get("duration"))
            self.FDuration:str = (time.strftime('%M:%S', time.gmtime(YT_extract.get("duration"))))

class TitleList:
    def __init__(self, url_list):
        self.Titles = []
        with YDL(ydl_opts) as ydl:
            if isinstance(url_list, str):
                YT_extract = ydl.extract_info(url_list, download=False)
                self.Titles.append(YT_extract.get("title", None))
            else:
                for i in range(len(url_list)):
                    YT_extract = ydl.extract_info(url_list[i], download=False)
                    self.Titles.append(YT_extract.get("title", None))

class music(commands.Cog):
    def __init__(self,client):
        self.client = client
        self.fvol = 0.25
        self.looper = False
        self.song_webpage_urls = []
        self.song_reqby=[]
        self.master_list=[self.song_webpage_urls,self.song_reqby]

    #Play
    @commands.command(pass_context=True, aliases=['p'])
    async def play(self, ctx,*,url:str=None):

        # Check if author in VC
        if ctx.author.voice is None or ctx.author.voice.channel is None:
            return await ctx.send("You are not connected to a voice channel.")

        # If player is_paused resume...
        if url is None:
            if self.song_webpage_urls !=[] and ctx.voice_client.is_paused() is True:
                async with ctx.typing():
                    ctx.voice_client.resume()
                    Resume = TitleList(self.song_webpage_urls[0])
                    embed=Embed(title='Resumed:',colour=0x4169e1)
                    embed.add_field(name=Resume.Titles[0],value='\u200b')
                    await ctx.send(embed=embed, delete_after=self.duration)
                    return await music.status_set(self, ctx)
            else: return await ctx.send('Queue is Empty.', delete_after = 60)

        # Join VC
        voice = get(self.client.voice_clients, guild=ctx.guild)
        if voice and voice.is_connected():
            pass
        elif voice==None:
            voiceChannel = ctx.message.author.voice.channel
            voice = await voiceChannel.connect()

        async with ctx.typing():
            #find vid url and add to list
            with YDL(ydl_opts) as ydl:
                if 'playlist' in url:
                    song_info = ydl.extract_info(f'{url}', download=False)['entries']
                    self.entries = len(song_info)
                    await ctx.send(f"Adding `{self.entries} SONGS` to Queue.")
                else:
                    song_info = ydl.extract_info(f'ytsearch:{url}', download=False)['entries']
                    self.entries = 1
                for i in range(0, self.entries):
                    self.song_webpage_urls.append(song_info[i].get("webpage_url"))
                    self.song_reqby.append(ctx.message.author.display_name)

            if 'playlist' not in url:
                Play = TitleList(self.song_webpage_urls[len(self.song_webpage_urls)-1])
                await ctx.send(f'Adding `{Play.Titles[0]}` to Queue.')

        if music.play_from_queue.is_running() is False:
            music.play_from_queue.start(self, ctx)

    #Status Update
    async def status_set(self, ctx):
        if ctx.voice_client is not None and self.song_webpage_urls:
            State = TitleList(self.song_webpage_urls[0])
            await self.client.change_presence(activity=Activity(type=ActivityType.streaming, name=State.Titles[0], platform='YouTube', url=self.song_webpage_urls[0]))
        else:
            await self.client.change_presence(status=Status.idle, activity=Activity(type=ActivityType.watching, name="my Homies."))

    #Queue
    @commands.command(aliases=['q'])
    async def queue(self, ctx):
        if len(self.song_webpage_urls)==0:
            await ctx.send('Queue is Empty.')
        else:
            async with ctx.typing():
                song = TitleList(self.song_webpage_urls)
            embed=Embed(title="Songs in Queue",colour=0xffa31a)
            embed.add_field(name='Now Playing',value=f'{song.Titles[0]} (Requested by {self.song_reqby[0]})', inline=False)
            if len(self.song_webpage_urls)>1:
                embed.add_field(name='Next in Queue',value=f'1. {song.Titles[1]} (Requested by {self.song_reqby[1]})', inline=False)
                for i in range(2,len(self.song_webpage_urls)):
                    embed.add_field(name='\u200b',value=f'{i}. {song.Titles[i]} (Requested by {self.song_reqby[i]})', inline=False)
            await ctx.send(embed=embed, delete_after=300)

    #Play from Queue
    @tasks.loop(seconds = 1)
    async def play_from_queue(self, ctx):
        # Embed
        if self.song_webpage_urls:
            PfQueue = video_info(self.song_webpage_urls[0])
            embed=Embed(title="", color=0xff0000)
            embed.set_thumbnail(url=f'{PfQueue.Thumbnail}')
            embed.set_author(name=f'Playing: {PfQueue.Title}', url=PfQueue.pURL, icon_url='')
            embed.add_field(name="Duration:", value=PfQueue.FDuration, inline=True)
            embed.add_field(name="Requested by:", value=self.song_reqby[0], inline=True)
            embed.add_field(name="Song Rating:", value=f'{PfQueue.Rating}/5', inline=True)
            await ctx.send(embed=embed, delete_after=PfQueue.Duration)
            await music.status_set(self, ctx)
            voice = get(self.client.voice_clients, guild=ctx.guild)
            voice.play(FFmpegPCMAudio(PfQueue.URL, **FFMPEG_OPTIONS))
            voice.source=PCMVolumeTransformer(voice.source)
            voice.source.volume = self.fvol
            self.duration = PfQueue.Duration
            while self.duration>0:
                await asyncio.sleep(1)
                self.duration=self.duration-1
            # list deletus
            if self.song_webpage_urls and self.looper:
                for i in self.master_list:
                    i.append(i[0])
                    i.pop(0)
            elif self.song_webpage_urls and not self.looper:
                for i in self.master_list:
                    i.pop(0)
        else: 
            self.fvol=0.25
            await music.status_set(self, ctx)
            await asyncio.sleep(30)
            await ctx.voice_client.disconnect()
            music.play_from_queue.cancel()

    #Skip
    @commands.command()
    async def skip(self, ctx, arg=0):
        if ctx.message.author.voice is None:
            return await ctx.send('You must be is same VC as the bot.')
        if ctx.voice_client is None:
            return await ctx.send('Bot is not connect to VC.')
        if ctx.message.author.voice is not None and ctx.voice_client is not None and self.song_webpage_urls:
            if ctx.voice_client.is_playing() is True or ctx.voice_client.is_paused() is True or ctx.voice_client is not None:
                embed=Embed(title='Removed',colour=0xff7f50)
                async with ctx.typing():
                    Skip = TitleList(self.song_webpage_urls[arg])
                if arg>0 and arg<len(self.song_webpage_urls):
                    embed.add_field(name=f'{Skip.Titles[0]} from Queue.',value=f'by {ctx.message.author.display_name}')
                    await ctx.send(embed=embed, delete_after=60)
                    for i in self.master_list:
                        i.pop(arg)
                elif arg==0:
                    if len(self.song_webpage_urls):
                        embed.add_field(name=f'{Skip.Titles[0]} from Queue.',value=f'by {ctx.message.author.display_name}')
                        ctx.voice_client.stop()
                        self.duration = 0
                        await ctx.send(embed=embed, delete_after=60)
                        await music.status_set(self, ctx)
                    else:
                        embed.add_field(name='Nothing',value=':p')
                        await ctx.send(embed=embed, delete_after=120)
        else: await ctx.send('Queue is Empty')

    #Stop
    @commands.command(aliases=['dc', 'kelambu'])
    async def stop(self, ctx):
        if ctx.message.author.voice is None:
            return await ctx.send('You must be is same VC as the bot.')
        if ctx.voice_client is None:
            return await ctx.send('Bot is not connect to VC.')
        if ctx.message.author.voice is not None and ctx.voice_client is not None:
            if ctx.voice_client.is_playing() is True or ctx.voice_client.is_paused() is True or ctx.voice_client is not None:
                ctx.voice_client.stop()
                # clean all lists
                for i in self.master_list:
                    i.clear()
                if music.play_from_queue.is_running() is True:
                    music.play_from_queue.cancel()
                await ctx.message.add_reaction('👋') ,await ctx.voice_client.disconnect()
                await music.status_set(self, ctx)
                self.looper=False
                self.fvol=0.25
            return await ctx.send('Thanks for Listening btw.')

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
                async with ctx.typing():
                    Pause = TitleList(self.song_webpage_urls[0])
                embed=Embed(title='Paused:',colour=0x4169e1)
                embed.add_field(name=Pause.Titles[0],value='\u200b')
                await ctx.send(embed=embed, delete_after=180)
                # we addin 1 every second to wait :p
                while ctx.voice_client.is_paused():
                    self.duration=self.duration+1
                    await asyncio.sleep(1)

    #Loop
    @commands.command(aliases=['repeat'])
    async def loop(self, ctx):
        if ctx.message.author.voice is None:
            return await ctx.send('You must be is same VC as the bot.')
        if ctx.voice_client is None:
            return await ctx.send('Bot is not connect to VC.')
        if ctx.message.author.voice is not None and ctx.voice_client is not None:
            if self.looper:
                self.looper=False
                embed=Embed(title='Loop Disabled.',colour=0x1abc9c)
            else:
                self.looper=True
                embed=Embed(title='Loop Enabled.',colour=0x800080)
            await ctx.send(embed=embed, delete_after=300)

    #Now PLaying
    @commands.command(aliases=['nowplaying'])
    async def np(self, ctx):
        if self.song_webpage_urls:
            NowPlaying = video_info(self.song_webpage_urls[0])
            percentile=20-round((self.duration/NowPlaying.Duration)*20)
            bar='────────────────────'
            progbar=bar[:percentile]+'⚪'+bar[percentile+1:]
            song_on = time.strftime('%M:%S', time.gmtime(NowPlaying.Duration-self.duration))
            embed=Embed(color=0xeb459e)
            embed.set_thumbnail(url=f'{NowPlaying.Thumbnail}')
            embed.set_author(name=f'{NowPlaying.Title}', url=NowPlaying.pURL, icon_url='')
            embed.add_field(name=f'{song_on} {progbar} {NowPlaying.FDuration}',value='\u200b',inline=False)
            embed.add_field(name="Views:", value=f'{human_format(NowPlaying.Views)}', inline=True)
            embed.add_field(name="Likes:", value=f'{human_format(NowPlaying.Likes)}', inline=True)
            embed.add_field(name="Uploaded on:", value=f'{NowPlaying.UploadDate}', inline=True)
            await ctx.send(embed=embed, delete_after=self.duration)
        else:
            await ctx.reply('Queue is Empty', delete_after=30)
            await ctx.message.delete()

    #Volume
    @commands.command(aliases=['vol','v'])
    async def volume(self, ctx, volu:int=None):
        if ctx.voice_client is None or ctx.message.author.voice is None:
            return await ctx.send('BRUH no.')
        if volu is None:
            return await ctx.send(f'Volume: {round(self.fvol*100)}%', delete_after=300)
        elif volu>0 and volu<=100:
            self.fvol=round(volu)/100
            ctx.voice_client.source.volume=self.fvol
            return await ctx.send(f'Volume is set to {round(self.fvol*100)}%', delete_after=300)
        else: await ctx.send("Set Volume between 1 and 100.", delete_after=30)

def setup(client):
	client.add_cog(music(client))
