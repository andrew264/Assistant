from discord.ext import commands, tasks
from discord.utils import get
from discord import FFmpegPCMAudio, PCMVolumeTransformer, Activity, ActivityType, Status, Embed
from olmusic import check_urls, human_format
import time
from datetime import datetime
import asyncio
import youtube_dl.YoutubeDL as YDL
ydl_opts = {
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'format': 'bestaudio/best',
}
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

song_webpage_urls=[]
song_titles=[]
song_urls=[]
song_thumbnails=[]
song_ratings=[]
song_views=[]
song_likes=[]
song_dates=[]
song_insec=[]
song_lengths=[]
song_reqby=[]
fvol=0.69420

master_list=[song_webpage_urls,song_titles,song_urls,song_thumbnails,song_ratings,song_views,song_likes,song_dates,song_insec,song_lengths,song_reqby]

looper=False

class music(commands.Cog):
    def __init__(self,client):
        self.client = client

    #Play
    @commands.command(pass_context=True, aliases=['p','P'])
    async def play(self, ctx,*,url:str=''):
        global song_webpage_urls, song_titles, song_urls, song_thumbnails, song_ratings, song_views, song_likes, song_dates, song_insec, song_lengths, song_reqby
        
        # Check if author in VC
        if ctx.author.voice is None or ctx.author.voice.channel is None:
            return await ctx.send("You are not connected to a voice channel.")

        # If player is_paused resume...
        if url=='' and ctx.voice_client.is_paused() is True:
            embed=Embed(title='Resumed:',colour=0x4169e1)
            embed.add_field(name=song_title_list[0],value='\u200b')
            await ctx.send(embed=embed, delete_after=30)
            await music.status_set(self, ctx)
            await ctx.message.delete()
            return ctx.voice_client.resume()

        #find vid url and add to list
        with YDL(ydl_opts) as ydl:
            try:
                song_info = ydl.extract_info(url, download=False)
            except:
                song_info = ydl.extract_info(f'ytsearch:{url}', download=False)['entries'][0]
            # Check for bad stuff
            if check_urls(song_info.get("webpage_url")):
                return await ctx.reply('Thats not a fucking song.')
            song_webpage_urls.append(song_info.get("webpage_url"))
            song_titles.append(song_info.get('title', None))
            song_urls.append(song_info["formats"][0]["url"])
            song_thumbnails.append(song_info.get("thumbnail"))
            song_ratings.append(round(song_info.get("average_rating"),2))
            song_views.append(song_info.get('view_count'))
            song_likes.append(song_info.get('like_count'))
            song_dates.append(datetime.strptime(song_info.get('upload_date'), '%Y%m%d').strftime('%d-%m-%Y'))
            song_insec.append(song_info.get("duration"))
            song_lengths.append(time.strftime('%M:%S', time.gmtime(song_info.get("duration"))))
            song_reqby.append(ctx.message.author.display_name)
        # Join VC
        voice = get(self.client.voice_clients, guild=ctx.guild)
        if voice and voice.is_connected():
            pass
        elif voice==None:
            voiceChannel = ctx.message.author.voice.channel
            voice = await voiceChannel.connect()
        # add to queue
        await ctx.send(f'Adding `{song_titles[len(song_titles)-1]}` to Queue.', delete_after=30)
        if music.play_from_queue.is_running() is False:
            music.play_from_queue.start(self, ctx)
        await asyncio.sleep(25)
        await ctx.message.delete()

    #Status Update
    async def status_set(self, ctx):
        if ctx.voice_client is not None and song_titles:
            await self.client.change_presence(activity=Activity(type=ActivityType.streaming, name=song_titles[0], details=song_lengths[0], platform='YouTube', url=song_webpage_urls[0]))
        else:
            await self.client.change_presence(status=Status.idle, activity=Activity(type=ActivityType.watching, name="my Homies."))

    #Queue
    @commands.command(aliases=['q'])
    async def queue(self, ctx):
        if len(song_titles)==0:
            await ctx.send('Queue is Empty.')
        else:
            embed=Embed(title="Songs in Queue",colour=0xffa31a)
            embed.add_field(name='Now Playing',value=f'{song_titles[0]} (Requested by {song_reqby[0]})', inline=False)
            if len(song_titles)>1:
                embed.add_field(name='Next in Queue',value=f'1. {song_titles[1]} (Requested by {song_reqby[1]})', inline=False)
                for i in range(2,len(song_titles)):
                    embed.add_field(name='\u200b',value=f'{i}. {song_titles[i]} (Requested by {song_reqby[i]})', inline=False)
            await ctx.message.delete()
            await ctx.send(embed=embed, delete_after=180)

    #Play from Queue
    @tasks.loop(seconds = 1)
    async def play_from_queue(self, ctx):
        global song_webpage_urls, song_titles, song_urls, song_thumbnails, song_ratings, song_views, song_likes, song_dates, song_insec, song_lengths, song_reqby, fvol
        # Embed
        if song_titles:
            embed=Embed(title="", color=0xff0000)
            embed.set_thumbnail(url=f'{song_thumbnails[0]}')
            embed.set_author(name=f'Playing: {song_titles[0]}', url=song_webpage_urls[0], icon_url='')
            embed.add_field(name="Duration:", value=song_lengths[0], inline=True)
            embed.add_field(name="Requested by:", value=song_reqby[0], inline=True)
            embed.add_field(name="Song Rating:", value=f'{song_ratings[0]}/5', inline=True)
            await ctx.send(embed=embed, delete_after=song_insec[0])
            await music.status_set(self, ctx)
            voice = get(self.client.voice_clients, guild=ctx.guild)
            voice.play(FFmpegPCMAudio(song_urls[0], **FFMPEG_OPTIONS))
            voice.source=PCMVolumeTransformer(voice.source)
            voice.source.volume = fvol
            # da timer
            global duration
            duration = song_insec[0]
            while duration>0:
                await asyncio.sleep(1)
                duration=duration-1
            # list deletus
            if song_titles and looper:
                for i in master_list:
                    i.append(i[0])
                    i.pop(0)
            elif song_titles and not looper:
                for i in master_list:
                    i.pop(0)
        else: 
            fvol=0.69420
            await music.status_set(self, ctx)
            await asyncio.sleep(9)
            await ctx.voice_client.disconnect()
            music.play_from_queue.cancel()

    #Skip
    @commands.command()
    async def skip(self, ctx, arg=0):
        global song_webpage_urls, song_titles, song_urls, song_thumbnails, song_ratings, song_views, song_likes, song_dates, song_insec, song_lengths, song_reqby, duration
        if ctx.message.author.voice is None:
            return await ctx.send('You must be is same VC as the bot.')
        if ctx.voice_client is None:
            return await ctx.send('Bot is not connect to VC.')
        if ctx.message.author.voice is not None and ctx.voice_client is not None:
            if ctx.voice_client.is_playing() is True or ctx.voice_client.is_paused() is True or ctx.voice_client is not None:
                embed=Embed(title='Removed',colour=0xff7f50)
                await ctx.message.delete()
                if arg>0 and arg<len(song_titles):
                    embed.add_field(name=f'{song_titles[arg]} from Queue.',value=f'by {ctx.message.author.display_name}')
                    await ctx.send(embed=embed, delete_after=60)
                    for i in master_list:
                        i.pop(arg)
                elif arg==0:
                    if len(song_titles):
                        embed.add_field(name=f'{song_titles[arg]} from Queue.',value=f'by {ctx.message.author.display_name}')
                        ctx.voice_client.stop()
                        duration = 1
                        await ctx.send(embed=embed, delete_after=60)
                        await music.status_set(self, ctx)
                    else:
                        embed.add_field(name='Nothing',value=':p')
                        await ctx.send(embed=embed, delete_after=30)
        else: await ctx.send('Queue is Empty')

    #Stop
    @commands.command(aliases=['dc', 'kelambu'])
    async def stop(self, ctx):
        global song_webpage_urls, song_titles, song_urls, song_thumbnails, song_ratings, song_views, song_likes, song_dates, song_insec, song_lengths, song_reqby, looper, fvol
        if ctx.message.author.voice is None:
            return await ctx.send('You must be is same VC as the bot.')
        if ctx.voice_client is None:
            return await ctx.send('Bot is not connect to VC.')
        if ctx.message.author.voice is not None and ctx.voice_client is not None:
            if ctx.voice_client.is_playing() is True or ctx.voice_client.is_paused() is True or ctx.voice_client is not None:
                ctx.voice_client.stop()
                # clean all lists
                for i in master_list:
                    i.clear()
                if music.play_from_queue.is_running() is True:
                    music.play_from_queue.cancel()
                await ctx.message.add_reaction('👋') ,await ctx.voice_client.disconnect()
                await music.status_set(self, ctx)
                looper=False
                fvol=0.69420
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
                embed.add_field(name=song_titles[0],value='\u200b')
                await ctx.send(embed=embed, delete_after=60)
                await ctx.message.delete()
                # we addin 1 every second to wait :p
                global duration
                while ctx.voice_client.is_paused():
                    duration=duration+1
                    await asyncio.sleep(1)

    #Loop
    @commands.command()
    async def loop(self, ctx):
        if ctx.message.author.voice is None:
            return await ctx.send('You must be is same VC as the bot.')
        if ctx.voice_client is None:
            return await ctx.send('Bot is not connect to VC.')
        if ctx.message.author.voice is not None and ctx.voice_client is not None:
            global looper
            if looper:
                looper=False
                embed=Embed(title='Loop Disabled.',colour=0xda70d6)
            else:
                looper=True
                embed=Embed(title='Loop Enabled.',colour=0x800080)
            await ctx.send(embed=embed, delete_after=60)
            await asyncio.sleep(30)
            await ctx.message.delete()

    #Now PLaying
    @commands.command()
    async def np(self, ctx):
        if song_titles:
            global duration
            percentile=30-round((duration/song_insec[0])*30)
            bar='──────────────────────────────'
            progbar=bar[:percentile]+'⚪'+bar[percentile+1:]
            song_on = time.strftime('%M:%S', time.gmtime(song_insec[0]-duration))
            await ctx.message.delete()
            embed=Embed(color=0x7fff00)
            embed.set_thumbnail(url=f'{song_thumbnails[0]}')
            embed.set_author(name=f'{song_titles[0]}', url=song_webpage_urls[0], icon_url='')
            embed.add_field(name=f'{song_on} {progbar} {song_lengths[0]}',value='\u200b',inline=False)
            embed.add_field(name="Views:", value=f'{human_format(song_views[0])}', inline=True)
            embed.add_field(name="Likes:", value=f'{human_format(song_likes[0])}', inline=True)
            embed.add_field(name="Uploaded on:", value=f'{song_dates[0]}', inline=True)
            await ctx.send(embed=embed, delete_after=duration)
            await asyncio.sleep(30)
            await ctx.message.delete()
        else:
            await ctx.reply('Queue is Empty', delete_after=30)
            await asyncio.sleep(30)
            await ctx.message.delete()

    #Volume
    @commands.command(aliases=['vol','v'])
    async def volume(self, ctx, volu:int=None):
        global fvol
        if ctx.voice_client is None or ctx.message.author.voice is None:
            return await ctx.send('BRUH no.')
        if volu is None:
            await ctx.send(f'Volume: {round(fvol*100)}%', delete_after=30)
            await asyncio.sleep(5)
            return await ctx.message.delete()
        elif volu>0 and volu<=100:
            fvol=round(volu)/100
            ctx.voice_client.source.volume=fvol
            await ctx.send(f'Volume is set to {round(fvol*100)}%', delete_after=30)
            await asyncio.sleep(5)
            return await ctx.message.delete()
        else: await ctx.send("Set Volume between 1 and 100.", delete_after=30)

def setup(client):
	client.add_cog(music(client))
