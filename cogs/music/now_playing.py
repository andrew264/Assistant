import asyncio
from typing import cast

import discord
import wavelink
from discord.ext import commands
from wavelink import Playable

from assistant import AssistantBot
from config import LavaConfig, HOME_GUILD_ID
from utils import check_vc, check_same_vc


class NowPlaying(commands.Cog):
    def __init__(self, bot: AssistantBot):
        self.bot = bot

    @commands.hybrid_command(name="nowplaying", aliases=["np", "now"], description="View the currently playing song")
    @commands.guild_only()
    @check_vc()
    @check_same_vc()
    async def nowplaying(self, ctx: commands.Context):
        assert ctx.guild
        vc: wavelink.Player = cast(wavelink.Player, ctx.voice_client)  # type: ignore
        if not vc.playing:
            await ctx.send("I am not playing anything right now.")
            return

        logger = self.bot.logger

        class NowPlayingView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=None)

            @staticmethod
            def format_time(ms: float) -> str:
                """Duration in HH:MM:SS Format"""
                seconds = ms / 1000
                if seconds > 3600:
                    return f'{int(seconds // 3600)}:{int((seconds % 3600) // 60):02}:{int(seconds % 60):02}'
                else:
                    return f'{int(seconds // 60):02}:{int(seconds % 60):02}'

            async def embed(self) -> discord.Embed:
                self.update_buttons()
                if not vc.current:
                    return discord.Embed(title="No Songs in Queue", description="use `/play` to add songs", )
                current_track: Playable = vc.current

                # if current_track.extra
                _embed = discord.Embed(colour=0x1ED760)
                if isinstance(current_track, wavelink.Playable):
                    _embed.set_author(name=current_track.title, url=current_track.uri, icon_url=current_track.artwork)
                    _embed.set_thumbnail(url=current_track.artwork)
                else:
                    _embed.set_author(name=current_track.title, url=current_track.uri)
                bar = "────────────────────"
                percentile = round((vc.position / current_track.length) * len(bar))
                progress_bar = bar[:percentile] + "⚪" + bar[percentile + 1:]
                song_on = self.format_time(vc.position)
                song_end = self.format_time(current_track.length)
                _embed.add_field(name=f"{song_on} {progress_bar} {song_end}", value="\u200b", inline=False, )

                # if isinstance(current_track, YTTrack):
                #     await current_track.fetch_info()
                #     _embed.add_field(name="Views:", value=f"{current_track.views}", inline=True)
                #     _embed.add_field(name="Likes:", value=f"{current_track.likes}", inline=True)
                #     _embed.add_field(name="Uploaded:", value=f"{current_track.upload_date}", inline=True)

                if not vc.queue.is_empty:
                    if vc.queue.mode is wavelink.QueueMode.loop_all:
                        _embed.set_footer(text=f"Looping through {vc.queue.count + 1} Songs")
                    elif vc.queue.mode is wavelink.QueueMode.normal:
                        in_queue_track: Playable = vc.queue.peek(0)
                        _embed.set_footer(text=f"Next in Queue: {in_queue_track.title}",
                                          icon_url=in_queue_track.artwork)
                else:
                    if vc.queue.mode is wavelink.QueueMode.loop_all:
                        _embed.set_footer(text="Looping current Song")
                    elif vc.queue.mode is wavelink.QueueMode.normal:
                        _embed.set_footer(text="No Songs in Queue")

                return _embed

            async def interaction_check(self, interaction: discord.Interaction) -> bool:
                assert isinstance(interaction.user, discord.Member)
                assert interaction.guild is not None
                if (not interaction.user.voice or not interaction.guild.voice_client or
                        interaction.user.voice.channel != interaction.guild.voice_client.channel):
                    await interaction.response.send_message(
                        content="You must be in the same VC as the bot to use this.",
                        ephemeral=True)
                    return False
                return True

            # Previous Button
            @discord.ui.button(custom_id="assistant:nowplaying:prev_button",
                               style=discord.ButtonStyle.primary, emoji="⏮️", )
            async def prev_button(self, interaction: discord.Interaction, button: discord.Button):
                assert vc.current is not None
                await vc.seek(0)
                await interaction.response.edit_message(embed=await self.embed())
                logger.debug(f"{interaction.user} skipped to beginning of {vc.current.title} in {interaction.guild}")

            # Rewind Button
            @discord.ui.button(custom_id="assistant:nowplaying:rewind_button",
                               style=discord.ButtonStyle.primary, emoji="⏪", )
            async def rewind_button(self, interaction: discord.Interaction, button: discord.Button):
                assert vc.current is not None
                if vc.position > 10000:
                    await vc.seek(vc.position - 10000)
                else:
                    await vc.seek(0)
                await interaction.response.edit_message(embed=await self.embed())
                logger.debug(f"{interaction.user} rewound 10 seconds in {vc.current.title} in {interaction.guild}")

            # Play/Pause Button
            @discord.ui.button(custom_id="assistant:nowplaying:pause_button",
                               style=discord.ButtonStyle.primary, emoji="⏸️", )
            async def play_button(self, interaction: discord.Interaction, button: discord.Button):
                assert vc.current is not None
                if not vc.paused:
                    await vc.pause(True)
                    button.emoji = "▶️"
                    button.style = discord.ButtonStyle.success
                    logger.debug(f"{interaction.user} paused {vc.current.title} in {interaction.guild}")
                else:
                    await vc.pause(False)
                    button.emoji = "⏸️"
                    button.style = discord.ButtonStyle.primary
                    logger.debug(f"{interaction.user} resumed {vc.current.title} in {interaction.guild}")
                await interaction.response.edit_message(view=self)

            # Fast Forward Button
            @discord.ui.button(custom_id="assistant:nowplaying:forward_button",
                               style=discord.ButtonStyle.primary, emoji="⏩", )
            async def forward_button(self, interaction: discord.Interaction, button: discord.Button):
                assert vc.current is not None
                if vc.position < vc.current.length - 10000:
                    await vc.seek(int(vc.position + 10000))
                else:
                    await vc.stop()
                await interaction.response.edit_message(embed=await self.embed())
                logger.debug(
                    f"{interaction.user} fast forwarded 10 seconds of {vc.current.title} in {interaction.guild}")

            # Skip Button
            @discord.ui.button(custom_id="assistant:nowplaying:skip_button",
                               style=discord.ButtonStyle.primary, emoji="⏭️", )
            async def skip_button(self, interaction: discord.Interaction, button: discord.Button):
                assert vc.current is not None
                logger.debug(f"{interaction.user} skipped {vc.current.title} in {interaction.guild}")
                await vc.stop()
                await interaction.response.edit_message(embed=await self.embed())

            # Stop Button
            @discord.ui.button(label="Stop", custom_id="assistant:nowplaying:stop_button",
                               style=discord.ButtonStyle.danger, emoji="⏹️", row=1, )
            async def stop_button(self, interaction: discord.Interaction, button: discord.Button):
                assert interaction.guild is not None
                vc.queue.clear()
                await vc.stop()
                if interaction.guild.voice_client:
                    await interaction.guild.voice_client.disconnect(force=True)
                await interaction.response.edit_message(content="Thanks for Listening", embed=None, view=None)
                logger.debug(f"{interaction.user} stopped the music in {interaction.guild}")

            # Repeat Button
            @discord.ui.button(label="Loop", custom_id="assistant:nowplaying:loop_button",
                               style=discord.ButtonStyle.gray, emoji="🔁", row=1, )
            async def loop_button(self, interaction: discord.Interaction, button: discord.Button):
                if vc.queue.mode.loop is wavelink.QueueMode.normal:
                    vc.queue.mode.loop = wavelink.QueueMode.loop_all
                    self.loop_button.emoji = "🔁"
                    logger.debug(f"{interaction.user} enabled looping in {interaction.guild}")
                else:
                    vc.queue.mode.loop = wavelink.QueueMode.normal
                    self.loop_button.emoji = "➡"
                    logger.debug(f"{interaction.user} disabled looping in {interaction.guild}")
                await interaction.response.edit_message(embed=await self.embed(), view=self)

            # Volume-down Button
            @discord.ui.button(custom_id="assistant:nowplaying:volume_down_button",
                               style=discord.ButtonStyle.green, emoji="➖", row=2, )
            async def volume_down(self, interaction: discord.Interaction, button: discord.Button):
                vol = vc.volume
                if vol > 10:
                    await vc.set_volume(max(vol - 10, 10))
                    self.volume_up.disabled = False
                else:
                    await vc.set_volume(10)
                button.disabled = True if vc.volume <= 10 else False
                self.volume.label = f"Volume: {vol} %"
                await interaction.response.edit_message(view=self)
                logger.debug(f"{interaction.user} set volume to {vol} % in {ctx.guild}")

            # Volume Button
            @discord.ui.button(label=f"Volume: {vc.volume} %", disabled=True,
                               style=discord.ButtonStyle.gray, row=2)
            async def volume(self, interaction: discord.Interaction, button: discord.Button):
                pass

            # Volume-up Button
            @discord.ui.button(custom_id="assistant:nowplaying:volume_up_button",
                               style=discord.ButtonStyle.green, emoji="➕", row=2, )
            async def volume_up(self, interaction: discord.Interaction, button: discord.Button):
                vol = vc.volume
                if vol <= 90:
                    await vc.set_volume(min(vol + 10, 100))
                    self.volume_down.disabled = False
                else:
                    await vc.set_volume(100)
                button.disabled = True if vol == 100 else False
                self.volume.label = f"Volume: {vol} %"
                await interaction.response.edit_message(view=self)
                logger.debug(f"{interaction.user} set volume to {vol} % in {ctx.guild}")

            def update_buttons(self):
                if vc.current is None and vc.queue.is_empty:
                    for button in self.children:
                        if isinstance(button, discord.ui.Button):
                            button.disabled = True
                    self.stop()
                    return
                # Play Button
                self.play_button.emoji = "▶️" if vc.paused else "⏸️"
                self.play_button.style = discord.ButtonStyle.success \
                    if vc.paused else discord.ButtonStyle.primary
                # Loop Button
                self.loop_button.emoji = "🔁" if vc.queue.mode.loop_all else "➡"
                # Volume Buttons
                current_volume: int = vc.volume
                self.volume.label = f"Volume: {current_volume} %"
                self.volume_down.disabled = True if current_volume <= 10 else False
                self.volume_up.disabled = True if current_volume == 100 else False

        view = NowPlayingView()
        msg = await ctx.send(embed=await view.embed(), view=view)
        if ctx.guild.id != HOME_GUILD_ID:
            return

        while True:
            await asyncio.sleep(7)
            try:
                await msg.edit(embed=await view.embed(), view=view)
            except discord.HTTPException:
                break
            while vc.paused or vc.current is None:
                await asyncio.sleep(1)
            if not vc.playing or not ctx.guild.me.voice:
                break
        try:
            await msg.delete()
        except discord.NotFound:
            pass


async def setup(bot: AssistantBot):
    if LavaConfig():
        await bot.add_cog(NowPlaying(bot))
