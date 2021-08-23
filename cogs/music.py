from discord.ext import commands, tasks
from discord.utils import get
from discord import FFmpegPCMAudio, PCMVolumeTransformer, Activity, ActivityType, Status, Embed
import time
from datetime import datetime
import asyncio
import re
import youtube_dl.YoutubeDL as YDL
ydl_opts = {
    'quiet': True,
    'no_warnings': True,
    'format': 'bestaudio/best',
}
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
vid_url_regex = re.compile(r"^(https?\:\/\/)?(www\.)?(youtube\.com|youtu\.?be)\/.+$", re.IGNORECASE)
playlist_url_regex = re.compile(r"^(https?\:\/\/)?(www\.)?(youtube\.com)\/(playlist).+$", re.IGNORECASE)

def human_format(num):
    num = float('{:.3g}'.format(num))
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])

class video_info:
    def __init__(self, YT_extract, author:str):
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
            self.Author:str = author

class music(commands.Cog):
    def __init__(self,client):
        self.client = client
        self.fvol = 0.25
        self.looper = False
        self.obj = []

    #Play
    @commands.command(pass_context=True, aliases=['p'])
    async def play(self, ctx,*,url:str=None):

        # Check if author in VC
        if ctx.author.voice is None or ctx.author.voice.channel is None:
            return await ctx.send("You are not connected to a voice channel.")

        # If player is_paused resume...
        if url is None:
            if self.obj !=[] and ctx.voice_client.is_paused() is True:
                async with ctx.typing():
                    ctx.voice_client.resume()
                    embed=Embed(title='Resumed:',colour=0x4169e1)
                    embed.add_field(name=self.obj[0].Title,value='\u200b')
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
                if re.match(playlist_url_regex, url) is not None:
                    song_info = ydl.extract_info(url, download=False)['entries']
                    entries = len(song_info)
                elif re.match(vid_url_regex, url) is not None:
                    song_info = []
                    song_info.append(ydl.extract_info(url, download=False))
                else:
                    song_info = ydl.extract_info(f'ytsearch:{url}', download=False)['entries']

            self.obj.append(video_info(song_info[0], ctx.message.author.display_name))

        if music.play_from_queue.is_running() is False:
            music.play_from_queue.start(self, ctx)

        if re.match(playlist_url_regex, url) is not None:
            await ctx.send(f"Adding `{entries} SONGS` to Queue.")
            for i in range(1,len(song_info)):
                self.obj.append(video_info(song_info[i], ctx.message.author.display_name))
        else: await ctx.send(f'Adding `{self.obj[len(self.obj)-1].Title}` to Queue.')

    #Status Update
    async def status_set(self, ctx):
        if ctx.voice_client is not None and self.obj:
            await self.client.change_presence(activity=Activity(type=ActivityType.streaming, name=self.obj[0].Title, platform='YouTube', url=self.obj[0].pURL))
        else:
            await self.client.change_presence(status=Status.idle, activity=Activity(type=ActivityType.watching, name="my Homies."))

    #Queue
    @commands.command(aliases=['q'])
    async def queue(self, ctx):
        if len(self.obj)==0:
            await ctx.send('Queue is Empty.')
        else:
            async with ctx.typing():
                embed=Embed(title="Songs in Queue",colour=0xffa31a)
                embed.add_field(name='Now Playing',value=f'{self.obj[0].Title} (Requested by {self.obj[0].Author})', inline=False)
                if len(self.obj)>1:
                    embed.add_field(name='Next in Queue',value=f'1. {self.obj[1].Title} (Requested by {self.obj[1].Author})', inline=False)
                    for i in range(2,len(self.obj)):
                        embed.add_field(name='\u200b',value=f'{i}. {self.obj[i].Title} (Requested by {self.obj[i].Author})', inline=False)
                return await ctx.send(embed=embed, delete_after=300)

    #Play from Queue
    @tasks.loop(seconds = 1)
    async def play_from_queue(self, ctx):
        # Embed
        if self.obj:
            embed=Embed(title="", color=0xff0000)
            embed.set_thumbnail(url=f'{self.obj[0].Thumbnail}')
            embed.set_author(name=f'Playing: {self.obj[0].Title}', url=self.obj[0].pURL, icon_url='')
            embed.add_field(name="Duration:", value=self.obj[0].FDuration, inline=True)
            embed.add_field(name="Requested by:", value=self.obj[0].Author, inline=True)
            embed.add_field(name="Song Rating:", value=f'{self.obj[0].Rating}/5', inline=True)
            await ctx.send(embed=embed, delete_after=self.obj[0].Duration)
            await music.status_set(self, ctx)
            voice = get(self.client.voice_clients, guild=ctx.guild)
            voice.play(FFmpegPCMAudio(self.obj[0].URL, **FFMPEG_OPTIONS))
            voice.source=PCMVolumeTransformer(voice.source)
            voice.source.volume = self.fvol
            self.duration = self.obj[0].Duration
            while self.duration>0:
                await asyncio.sleep(1)
                self.duration=self.duration-1
            # song ends here
            if self.obj and self.looper:
                self.obj.append(self.obj[0])
                self.obj.pop(0)
            elif self.obj and not self.looper:
                self.obj.pop(0)
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
        if ctx.message.author.voice is not None and ctx.voice_client is not None and self.obj:
            if ctx.voice_client.is_playing() is True or ctx.voice_client.is_paused() is True or ctx.voice_client is not None:
                embed=Embed(title='Removed',colour=0xff7f50)
                embed.add_field(name=f'{self.obj[arg].Title} from Queue.',value=f'by {ctx.message.author.display_name}')
                if arg>0 and arg<len(self.obj):
                    await ctx.send(embed=embed, delete_after=60)
                    self.obj.pop(arg)
                elif arg==0:
                    ctx.voice_client.stop()
                    self.duration = 0
                    await ctx.send(embed=embed, delete_after=60)
                    await music.status_set(self, ctx)
                else:
                    embed.add_field(name='Nothing',value=':p')
                    await ctx.send(embed=embed, delete_after=30)
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
                if music.play_from_queue.is_running() is True:
                    music.play_from_queue.cancel()
                # clean list
                self.obj.clear()
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
                embed=Embed(title='Paused:',colour=0x4169e1)
                embed.add_field(name=self.obj[0].Title,value='\u200b')
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
        if self.obj:
            percentile=20-round((self.duration/self.obj[0].Duration)*20)
            bar='────────────────────'
            progbar=bar[:percentile]+'⚪'+bar[percentile+1:]
            song_on = time.strftime('%M:%S', time.gmtime(self.obj[0].Duration-self.duration))
            embed=Embed(color=0xeb459e)
            embed.set_thumbnail(url=f'{self.obj[0].Thumbnail}')
            embed.set_author(name=f'{self.obj[0].Title}', url=self.obj[0].pURL, icon_url='')
            embed.add_field(name=f'{song_on} {progbar} {self.obj[0].FDuration}',value='\u200b',inline=False)
            embed.add_field(name="Views:", value=f'{human_format(self.obj[0].Views)}', inline=True)
            embed.add_field(name="Likes:", value=f'{human_format(self.obj[0].Likes)}', inline=True)
            embed.add_field(name="Uploaded on:", value=f'{self.obj[0].UploadDate}', inline=True)
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
