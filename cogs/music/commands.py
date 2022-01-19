# Imports
import asyncio

import lavalink
from disnake import (
    Activity,
    ActivityType,
    Client,
    Status,
    NotFound,
)
from disnake.ext import commands
from disnake.utils import get

from cogs.music.fetch import (
    FindInputType,
    InputType,
    FetchVideo,
    Search,
    FetchPlaylist,
)
from cogs.music.lavaclient import LavalinkVoiceClient
from cogs.music.misc import AddTagstoJSON
from cogs.music.nowplaying import NowPlayingButtons
from cogs.music.queue import QueuePages, QueueEmbed

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -multiple_requests 1",
    "options": "-vn",
}


class Music(commands.Cog):
    def __init__(self, client: Client):
        self.client = client

        if not hasattr(client, 'lavalink'):  # This ensures the client isn't overwritten during cog reloads.
            client.lavalink = lavalink.Client(client.user.id)
            client.lavalink.add_node('127.0.0.1', 2333, 'youshallnotpass', 'in', 'assistant-node')

        lavalink.add_event_hook(self.track_hook)

    def cog_unload(self):
        """ Cog unload handler. This removes any event hooks that were registered. """
        self.client.lavalink._event_hooks.clear()

    async def track_hook(self, event):
        # Update client's status
        # Cuz why not ?
        if isinstance(event, lavalink.events.TrackStartEvent):
            song = event.player.current
            if song:
                await self.client.change_presence(activity=Activity(type=ActivityType.listening,
                                                                    name=song.Title, ))
        if isinstance(event, lavalink.events.QueueEndEvent):
            await self.client.change_presence(status=Status.online, activity=Activity(type=ActivityType.watching,
                                                                                      name="yall Homies."), )

    # Play
    @commands.command(pass_context=True, aliases=["p"])
    @commands.guild_only()
    async def play(self, ctx: commands.Context, *, query: str = None) -> None:

        player = self.client.lavalink.player_manager.create(ctx.guild.id, endpoint=str(ctx.guild.region))

        # If player is_paused resume...
        if query is None:
            if player.current and player.paused:
                if ctx.voice_client is None:
                    return
                await self.pause(ctx)
                return
            else:
                await ctx.send("Nothing to Play")
                return

        async with ctx.typing():
            input_type = FindInputType(query)
            loop = asyncio.get_event_loop()
            match input_type:
                case InputType.Playlist:
                    await FetchPlaylist(query, ctx.author, player)
                case InputType.Search:
                    await Search(query, ctx.author, player)
                case InputType.URL:
                    await FetchVideo(query, ctx.author, player)

        if input_type == InputType.Playlist:
            await ctx.send(f"Adding Playlist to Queue...")
        else:
            await ctx.send(f"Adding `{player.queue[-1].Title}` to Queue.")

        # Join VC
        voice = get(self.client.voice_clients, guild=ctx.guild)
        if voice and player.is_connected:
            pass
        elif voice is None:
            player.store('channel', ctx.channel.id)
            await ctx.author.voice.channel.connect(cls=LavalinkVoiceClient)

        if player.queue and not player.is_playing:
            await player.play()
            await player.set_volume(25)

    # Queue
    @commands.command(aliases=["q"])
    @commands.guild_only()
    async def queue(self, ctx: commands.Context) -> None:
        player = self.client.lavalink.player_manager.get(ctx.guild.id)
        view = QueuePages(player)
        view.message = await ctx.send(embed=QueueEmbed(player, 1), view=view)

    # Skip
    @commands.command()
    @commands.guild_only()
    async def skip(self, ctx: commands.Context, arg: int = 0) -> None:
        player = self.client.lavalink.player_manager.get(ctx.guild.id)
        if not player.is_playing or arg > len(player.queue):
            return
        if 0 < arg <= len(player.queue):
            await ctx.send(f"{ctx.author.display_name} removed `{player.queue[arg - 1].Title}` from Queue.")
            player.queue.pop(arg)
        elif arg == 0:
            await ctx.send(f"{ctx.author.display_name} removed `{player.current.Title}` from Queue.")
            await player.skip()

    # Stop
    @commands.command(aliases=["dc", "kelambu"])
    @commands.guild_only()
    async def stop(self, ctx: commands.Context) -> None:
        player = self.client.lavalink.player_manager.get(ctx.guild.id)
        if player.is_playing or player.paused:
            # Clear the queue to ensure old tracks don't start playing
            # when someone else queues something.
            player.queue.clear()
            # Stop the current track so Lavalink consumes less resources.
            await player.stop()
            # Disconnect from the voice channel.
            await ctx.voice_client.disconnect(force=True)
        await ctx.message.add_reaction("👋")

    # Pause
    @commands.command()
    @commands.guild_only()
    async def pause(self, ctx: commands.Context) -> None:
        player = self.client.lavalink.player_manager.get(ctx.guild.id)
        if player.paused is False:
            await player.set_pause(pause=True)
            await ctx.send(f"{ctx.author.display_name} paused `{player.current.Title}`")
        else:
            await player.set_pause(pause=False)
            await ctx.send(f"{ctx.author.display_name} resumed `{player.current.Title}`")

    # Loop
    @commands.command(aliases=["repeat"])
    @commands.guild_only()
    async def loop(self, ctx: commands.Context) -> None:
        player = self.client.lavalink.player_manager.get(ctx.guild.id)
        if player.repeat:
            player.set_repeat(False)
            await ctx.send("Loop Disabled")
        else:
            player.set_repeat(True)
            await ctx.send("Loop Enabled")

    # Now Playing
    @commands.command(aliases=["np"])
    @commands.guild_only()
    async def nowplaying(self, ctx: commands.Context) -> None:
        player = self.client.lavalink.player_manager.get(ctx.guild.id)
        await ctx.message.delete()
        if not player.is_playing:
            await ctx.send("Queue is Empty", delete_after=30)
            return
        view = NowPlayingButtons(player)
        msg = await ctx.send(embed=view.NPEmbed(), view=view)
        view.message = msg
        while True:
            if player.is_playing and ctx.voice_client:
                pass
            else:
                try:
                    await msg.delete()
                except NotFound:
                    pass
                break
            await msg.edit(embed=view.NPEmbed())
            await asyncio.sleep(5)

    # Jump
    @commands.command(aliases=["skipto"])
    @commands.guild_only()
    async def jump(self, ctx: commands.Context, song_index: int = 1) -> None:
        player = self.client.lavalink.player_manager.get(ctx.guild.id)
        if ctx.voice_client and player.is_playing and song_index >= 1:
            del player.queue[0:song_index - 1]
        await ctx.send("Skipped")
        await player.play()

    # Volume
    @commands.command(aliases=["vol", "v"])
    @commands.guild_only()
    async def volume(self, ctx: commands.Context, volume_int: int = None) -> None:
        player = self.client.lavalink.player_manager.get(ctx.guild.id)
        if volume_int is None:
            await ctx.send(f"Volume: {player.volume}%")
        elif 0 < volume_int <= 100:
            try:
                await player.set_volume(round(volume_int))
                await ctx.send(f"Volume is set to `{round(volume_int)}%`")
            except AttributeError:
                pass
        else:
            await ctx.send("Set Volume between `1 and 100`.")

    # Add Tags to Current Song
    @commands.is_owner()
    @commands.guild_only()
    @commands.command(aliases=["tag"])
    async def addtag(self, ctx: commands.Context, *, tag: str) -> None:
        player = self.client.lavalink.player_manager.get(ctx.guild.id)
        AddTagstoJSON(player.current.identifier, tag)
        await ctx.reply(f"TAG: **{tag}** added to **{player.current.Title}**")

    # Check Bot in VC
    @queue.before_invoke
    @skip.before_invoke
    @stop.before_invoke
    @pause.before_invoke
    @loop.before_invoke
    @nowplaying.before_invoke
    @jump.before_invoke
    @addtag.before_invoke
    @volume.before_invoke
    async def check_voice(self, ctx: commands.Context) -> None:
        player = self.client.lavalink.player_manager.get(ctx.guild.id)
        if ctx.voice_client is None or not player.is_connected:
            raise commands.CheckFailure("Bot is not connect to VC.")
        if ctx.author.voice is None:
            raise commands.CheckFailure("You are not connected to a voice channel.")
        if ctx.voice_client is not None and ctx.author.voice is not None:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                raise commands.CheckFailure("You must be in same VC as Bot.")

    # Play Checks
    @play.before_invoke
    async def check_play(self, ctx: commands.Context) -> None:
        if ctx.author.voice is None:
            raise commands.CheckFailure("You are not connected to a voice channel.")
        if ctx.voice_client is not None and ctx.author.voice is not None:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                raise commands.CheckFailure("You must be in same VC as Bot.")
        permissions = ctx.author.voice.channel.permissions_for(ctx.me)
        if not permissions.connect or not permissions.speak:
            raise commands.CheckFailure('Missing `CONNECT` and `SPEAK` permissions.')


def setup(client):
    client.add_cog(Music(client))
