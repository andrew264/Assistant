from typing import Optional

import wavelink
from discord import app_commands
from discord.ext import commands

from assistant import AssistantBot
from config import LavaConfig, OWNER_ID
from utils import check_vc, check_same_vc, clickable_song


class MusicCommands(commands.Cog):
    def __init__(self, bot: AssistantBot):
        self.bot = bot

    @commands.hybrid_command(name="skip", aliases=["s", "next"], description="Skip songs that are in queue")
    @commands.guild_only()
    @check_vc()
    @check_same_vc()
    @app_commands.describe(index="Index of the song to skip")
    async def skip(self, ctx: commands.Context, index: int = 0):
        vc: wavelink.Player = ctx.voice_client  # type: ignore
        if not vc.is_playing():
            await ctx.send("I am not playing anything right now.")
            return
        if index == 0:
            await ctx.send(f"Skipping {clickable_song(vc.current)}", suppress_embeds=True)
            await vc.stop()
            return
        if index > vc.queue.count or index < 0:
            await ctx.send("Invalid index")
            return
        else:
            await ctx.send(f"Skipping {clickable_song(vc.queue[index - 1])}", suppress_embeds=True)
            del vc.queue[index - 1]

    @commands.hybrid_command(name="loop", aliases=["l"], description="Loop the current song")
    @commands.guild_only()
    @check_vc()
    @check_same_vc()
    async def loop(self, ctx: commands.Context):
        vc: wavelink.Player = ctx.voice_client  # type: ignore
        if not vc.is_playing():
            await ctx.send("I am not playing anything right now.")
            return
        if vc.queue.loop:
            vc.queue.loop = False
            await ctx.send("Looping is now disabled.")
        else:
            vc.queue.loop = True
            await ctx.send("Looping is now enabled.")

    @commands.hybrid_command(name="volume", aliases=["v", "vol"], description="Change the volume")
    @commands.guild_only()
    @check_vc()
    @check_same_vc()
    @app_commands.describe(volume="Volume to set [0 - 100]")
    async def volume(self, ctx: commands.Context, volume: int):
        vc: wavelink.Player = ctx.voice_client  # type: ignore
        if not vc.is_playing():
            await ctx.send("I am not playing anything right now.")
            return
        if ctx.author.id == OWNER_ID:
            await vc.set_volume(volume)
            await ctx.send(f"Volume set to `{volume} %`")
            return
        if volume < 0 or volume > 100:
            await ctx.send("Invalid volume")
            return
        await vc.set_volume(volume)
        await ctx.send(f"Volume set to `{volume} %`")

    @commands.hybrid_command(name="stop", aliases=["leave", "disconnect", "dc"],
                             description="Stops the music and disconnects the bot from the voice channel")
    @commands.guild_only()
    @check_vc()
    @check_same_vc()
    async def stop(self, ctx: commands.Context):
        assert ctx.guild
        vc: wavelink.Player = ctx.voice_client  # type: ignore
        if not vc or not vc.is_connected() or not ctx.guild.voice_client:
            return await ctx.send("I am not connected to a voice channel", ephemeral=True)
        vc.queue.reset()
        await vc.stop()
        await ctx.guild.voice_client.disconnect(force=True)
        await ctx.send("Thanks for Listening")

    @commands.hybrid_command(name="skipto", aliases=["st"], description="Skip to a specific song in the queue")
    @commands.guild_only()
    @check_vc()
    @check_same_vc()
    @app_commands.describe(index="Index of the song to skip to")
    async def skipto(self, ctx: commands.Context, index: int = 0):
        vc: wavelink.Player = ctx.voice_client  # type: ignore
        if not vc.is_playing():
            await ctx.send("I am not playing anything right now.")
            return
        if index == 0:
            await ctx.send(f"Skipping {clickable_song(vc.current)}", suppress_embeds=True)
            await vc.stop()
            return
        if index >= vc.queue.count or index < 0:
            await ctx.send("Invalid index")
            return
        else:
            await ctx.send(f"Skipping to {clickable_song(vc.queue[index - 1])}", suppress_embeds=True)
            vc.queue.queue.rotate(-(index - 1))
            await vc.stop()

    @commands.hybrid_command(name="seek", description="Seek to a specific time in the song")
    @commands.guild_only()
    @check_vc()
    @check_same_vc()
    @app_commands.describe(time="Time to seek to in MM:SS format")
    async def seek(self, ctx: commands.Context, time: Optional[str] = None):
        vc: wavelink.Player = ctx.voice_client  # type: ignore
        if not vc.is_playing():
            await ctx.send("I am not playing anything right now.")
            return
        if not time:
            await vc.seek(0)

        def time_in_seconds(timestamp: str) -> int:
            """
            Converts a timestamp string to seconds.
            """
            time_components = timestamp.split(':') if ':' in timestamp else timestamp.split('.')
            time_components = [int(comp) for comp in time_components]

            if any(comp < 0 or comp >= 60 for comp in time_components):
                return 0

            seconds = sum(comp * 60 ** (len(time_components) - idx - 1) for idx, comp in enumerate(time_components))
            return seconds

        await vc.seek(time_in_seconds(time) * 1000)
        await ctx.send(f"Seeked to {time}")


async def setup(bot: AssistantBot):
    if LavaConfig():
        await bot.add_cog(MusicCommands(bot))
