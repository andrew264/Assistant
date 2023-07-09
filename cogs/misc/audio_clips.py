import os
import random
from typing import Optional, List

import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands
from thefuzz import process

from assistant import AssistantBot
from config import RESOURCE_PATH
from utils import check_vc

GUILDS: List[discord.Object] = []


class Clips(commands.Cog):
    def __init__(self, bot: AssistantBot):
        self.bot = bot

    @app_commands.command(name='clips', description='Play a audio clip in the voice channel', )
    @app_commands.describe(clip='Which clip should I play?')
    # @app_commands.guilds(*GUILDS)
    @check_vc()
    async def clips(self, ctx: discord.Interaction, clip: str):
        assert ctx.guild is not None
        if clip is None:
            await ctx.response.send_message(content="Please specify a clip.")
            return
        if not os.path.exists(RESOURCE_PATH / 'audio_clips' / str(ctx.guild.id) / clip):
            await ctx.response.send_message(content="Clip not found.")
            return
        await ctx.response.defer()

        voice: Optional[discord.VoiceClient] = discord.utils.get(self.bot.voice_clients,  # type: ignore
                                                                 guild=ctx.guild)
        last_clip: str = clip

        def play(_clip: Optional[str] = None) -> None:
            nonlocal last_clip
            if not (voice or voice.is_connected() or last_clip):
                return
            voice.stop()
            if _clip:
                last_clip = _clip
            try:
                assert ctx.guild is not None
                audio_file = RESOURCE_PATH / 'audio_clips' / str(ctx.guild.id) / last_clip
                voice.play(discord.FFmpegPCMAudio(audio_file.as_posix()))
            except discord.ClientException:
                pass

        class RepeatStopView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)

            @discord.ui.button(label='Repeat', style=discord.ButtonStyle.secondary)
            async def repeat_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                assert interaction.guild is not None
                assert last_clip is not None
                if interaction.guild.voice_client is None:
                    await interaction.response.edit_message(
                        content="Disconnected form Voice. Use `/clip` to play clips.", view=None)
                    self.stop()
                    return
                play()
                await interaction.response.edit_message(content=f"Playing clip: `{last_clip[:-4]}`")

            @discord.ui.button(label='Stop', style=discord.ButtonStyle.danger)
            async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                assert interaction.guild is not None
                if interaction.guild.voice_client is None:
                    await interaction.response.edit_message(
                        content="Disconnected form Voice. Use `/clip` to play clips.", view=None)
                    self.stop()
                    return
                voice.stop()
                if voice.is_connected():
                    await voice.disconnect()
                await interaction.response.edit_message(content=f"kthxbye...", view=None)
                self.stop()

        if voice is None:
            voice_channel: discord.VoiceChannel = ctx.user.voice.channel  # type: ignore
            voice: discord.VoiceClient = await voice_channel.connect()

        play(clip)
        await ctx.edit_original_response(content=f"Playing clip: `{clip[:-4]}`", view=RepeatStopView())

    @clips.autocomplete('clip')
    async def clip_autocomplete(self, ctx: discord.Interaction, clip: str) -> List[Choice]:
        assert ctx.guild is not None
        clips_dir = RESOURCE_PATH / 'audio_clips' / str(ctx.guild.id)
        if not os.path.exists(clips_dir):
            return []
        all_clips = [c for c in os.listdir(clips_dir) if c.endswith('.mp3')]
        if clip == '':
            return [Choice(name=c[:-4], value=c) for c in random.sample(all_clips, 25)]
        return [Choice(name=c[0][:-4], value=c[0]) for c in process.extract(query=clip, choices=all_clips, limit=5)]


async def setup(bot: AssistantBot):
    if not os.path.exists(RESOURCE_PATH / 'audio_clips'):
        bot.logger.warning(f"[FAILED] audio clips not found at {RESOURCE_PATH / 'audio_clips'}, loading skipped")
        return
    global GUILDS
    GUILDS = list(discord.Object(id=int(f.name)) for f in os.scandir(RESOURCE_PATH / 'audio_clips') if f.is_dir())
    bot.logger.info(f"[LOADED] audio clips {len(GUILDS)} {'guilds' if len(GUILDS) > 1 else 'guild'}")
    await bot.add_cog(Clips(bot))
