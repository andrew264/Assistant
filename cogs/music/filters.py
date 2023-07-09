from typing import Optional

import discord
import wavelink
from discord.ext import commands

from assistant import AssistantBot
from utils import check_vc, check_same_vc


class Filters(commands.Cog):
    def __init__(self, bot: AssistantBot):
        self.bot = bot

    @commands.hybrid_group(name="filters", aliases=['f'], description="Change the filters of the player")
    @commands.guild_only()
    @check_vc()
    @check_same_vc()
    async def filters(self, ctx: commands.Context):
        pass

    @filters.command(name="nightcore", aliases=['nc'], description="Enable/Disable nightcore filter")
    @check_vc()
    @check_same_vc()
    async def nightcore(self, ctx: commands.Context):
        vc: wavelink.Player = ctx.voice_client  # type: ignore
        # check if nightcore filter is already enabled
        if vc._filter and vc._filter.timescale and vc._filter.timescale.name == "nightcore":
            await vc.set_filter(wavelink.Filter(vc._filter,
                                                timescale=wavelink.Timescale()))
            await ctx.send("Disabled nightcore filter.")
            return
        ts = wavelink.Timescale(speed=1.2999, pitch=1.2999, rate=1.0)
        ts.name = "nightcore"
        _filter = wavelink.Filter(timescale=ts)
        await vc.set_filter(_filter)
        await ctx.send("Enabled nightcore filter.")

    @filters.command(name="vaporwave", aliases=['vw'], description="Enable/Disable vaporwave filter")
    async def vaporwave(self, ctx: commands.Context):
        vc: wavelink.Player = ctx.voice_client  # type: ignore
        # check if vaporwave filter is already enabled
        if vc._filter and vc._filter.tremolo and vc._filter.tremolo.name == 'vaporwave':
            await vc.set_filter(wavelink.Filter(vc._filter,
                                                equalizer=wavelink.Equalizer(bands=[(0, 0.0), (1, 0.0)]),
                                                timescale=wavelink.Timescale(),
                                                tremolo=wavelink.Tremolo()))
            await ctx.send("Disabled vaporwave filter.")
            return
        ts = wavelink.Timescale(speed=1.0, pitch=0.8500, rate=1.0)
        ts.name = "vaporwave"
        tremolo = wavelink.Tremolo(frequency=14.0, depth=0.3)
        tremolo.name = "vaporwave"
        _filter = wavelink.Filter(equalizer=wavelink.Equalizer(bands=[(0, 0.3), (1, 0.3)]),
                                  timescale=ts,
                                  tremolo=tremolo)
        await vc.set_filter(_filter)
        await ctx.send("Enabled vaporwave filter.")

    @filters.command(name="bass", aliases=['bb', 'bassboost'], description="Enable/Disable Bass-Boost filter")
    async def bass_boost(self, ctx: commands.Context):
        vc: wavelink.Player = ctx.voice_client  # type: ignore

        class BassBoostButtons(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=180)
                self.message: Optional[discord.Message] = None

            async def interaction_check(self, interaction: discord.Interaction) -> bool:
                assert isinstance(interaction.user, discord.Member)
                assert interaction.guild
                if interaction.user.voice is None:
                    await interaction.response.send_message("You are not connected to a voice channel.", ephemeral=True)
                    return False
                if interaction.guild.voice_client is None:
                    await interaction.response.send_message("leave me alone")
                    return False
                if interaction.user.voice.channel == interaction.guild.voice_client.channel:
                    return True
                await interaction.response.send_message("You must be in same VC as Bot.", ephemeral=True)
                return False

            async def on_timeout(self) -> None:
                self.stop()
                if self.message is not None:
                    try:
                        await self.message.delete()
                    except discord.NotFound:
                        pass

            @staticmethod
            async def _update_eq(bands: list) -> None:
                # update the EQ filter
                eq = wavelink.Equalizer(bands=bands)
                await vc.set_filter(wavelink.Filter(vc._filter, equalizer=eq))

            @discord.ui.button(label="off", style=discord.ButtonStyle.gray)
            async def bass_off(self, interaction: discord.Interaction, button: discord.Button):
                await self._update_eq([(0, 0.0), (1, 0.0)])
                embed = discord.Embed(title="Bass Boost Disabled", colour=0x000000)
                await interaction.response.edit_message(embed=embed, view=self)

            @discord.ui.button(label="low", style=discord.ButtonStyle.green)
            async def bass_low(self, interaction: discord.Interaction, button: discord.Button):
                await self._update_eq([(0, 0.2), (1, 0.15)])
                embed = discord.Embed(title="Bass Boost set to Low", colour=0x00FF00)
                await interaction.response.edit_message(embed=embed, view=self)

            @discord.ui.button(label="medium", style=discord.ButtonStyle.blurple)
            async def bass_mid(self, interaction: discord.Interaction, button: discord.Button, ):
                await self._update_eq([(0, 0.4), (1, 0.25)])
                embed = discord.Embed(title="Bass Boost set to Medium", colour=0x0000FF)
                await interaction.response.edit_message(embed=embed, view=self)

            @discord.ui.button(label="high", style=discord.ButtonStyle.danger)
            async def bass_hi(self, interaction: discord.Interaction, button: discord.Button, ):
                await self._update_eq([(0, 0.6), (1, 0.4)])
                embed = discord.Embed(title="Bass Boost set to High", colour=0xFF0000)
                await interaction.response.edit_message(embed=embed, view=self)

        _embed = discord.Embed(title="Bass Boost", colour=0x000000)
        view = BassBoostButtons()
        view.message = await ctx.send(embed=_embed, view=view)

    @filters.command(name="treble", aliases=['tb', 'trebleboost'], description="Enable/Disable Treble-Boost filter")
    async def treble_boost(self, ctx: commands.Context):
        vc: wavelink.Player = ctx.voice_client  # type: ignore

        class TrebleBoostButtons(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=180)
                self.message: Optional[discord.Message] = None

            async def interaction_check(self, interaction: discord.Interaction) -> bool:
                assert isinstance(interaction.user, discord.Member)
                assert interaction.guild
                if interaction.user.voice is None:
                    await interaction.response.send_message("You are not connected to a voice channel.", ephemeral=True)
                    return False
                if interaction.guild.voice_client is None:
                    await interaction.response.send_message("leave me alone")
                    return False
                if interaction.user.voice.channel == interaction.guild.voice_client.channel:
                    return True
                await interaction.response.send_message("You must be in same VC as Bot.", ephemeral=True)
                return False

            async def on_timeout(self) -> None:
                self.stop()
                if self.message is not None:
                    try:
                        await self.message.delete()
                    except discord.NotFound:
                        pass

            @staticmethod
            async def _update_eq(bands: list) -> None:
                # update the EQ filter
                eq = wavelink.Equalizer(bands=bands)
                await vc.set_filter(wavelink.Filter(vc._filter, equalizer=eq))

            @discord.ui.button(label="off", style=discord.ButtonStyle.gray)
            async def treble_off(self, interaction: discord.Interaction, button: discord.Button):
                await self._update_eq([(10, 0.0), (11, 0.0), (12, 0.0), (13, 0.0)])
                embed = discord.Embed(title="Treble Boost Disabled", colour=0x000000)
                await interaction.response.edit_message(embed=embed, view=self)

            @discord.ui.button(label="low", style=discord.ButtonStyle.green)
            async def treble_low(self, interaction: discord.Interaction, button: discord.Button):
                await self._update_eq([(10, 0.2), (11, 0.2), (12, 0.2), (13, 0.25)])
                embed = discord.Embed(title="Treble Boost set to Low", colour=0x00FF00)
                await interaction.response.edit_message(embed=embed, view=self)

            @discord.ui.button(label="medium", style=discord.ButtonStyle.blurple)
            async def treble_mid(self, interaction: discord.Interaction, button: discord.Button):
                await self._update_eq([(10, 0.4), (11, 0.4), (12, 0.4), (13, 0.45)])
                embed = discord.Embed(title="Treble Boost set to Medium", colour=0x0000FF)
                await interaction.response.edit_message(embed=embed, view=self)

            @discord.ui.button(label="high", style=discord.ButtonStyle.danger)
            async def treble_hi(self, interaction: discord.Interaction, button: discord.Button):
                await self._update_eq([(10, 0.6), (11, 0.6), (12, 0.6), (13, 0.65)])
                embed = discord.Embed(title="Treble Boost set to High", colour=0xFF0000)
                await interaction.response.edit_message(embed=embed, view=self)

        _embed = discord.Embed(title="Treble Boost", colour=0x000000)
        view = TrebleBoostButtons()
        view.message = await ctx.send(embed=_embed, view=view)

    @filters.command(name="8d", aliases=['surround', '3d'], description="Enable/Disable 8D filter")
    async def eight_d(self, ctx: commands.Context):
        vc: wavelink.Player = ctx.voice_client  # type: ignore
        # check if 8D filter is already enabled
        if vc._filter and vc._filter.rotation and vc._filter.rotation.name == "rotation_8d":
            await vc.set_filter(wavelink.Filter(vc._filter,
                                                rotation=wavelink.Rotation()))
            await ctx.send("Disabled 8D filter.")
            return
        r8d = wavelink.Rotation(speed=0.2)
        r8d.name = "rotation_8d"
        await vc.set_filter(wavelink.Filter(vc._filter, rotation=r8d))
        await ctx.send("Enabled 8D filter.")

    @filters.command(name="timescale", aliases=['ts', 'speed', 'pitch'], description="Enable/Disable timescale filter")
    async def timescale(self, ctx: commands.Context):
        vc: wavelink.Player = ctx.voice_client  # type: ignore
        if vc._filter and vc._filter.timescale and vc._filter.timescale.name == "timescale":
            ts = vc._filter.timescale
        else:
            ts = wavelink.Timescale()
            ts.name = "timescale"

        class TimeScaleButtons(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=180)
                self.step: float = 0.1
                self.message: Optional[discord.Message] = None

            async def interaction_check(self, interaction: discord.Interaction) -> bool:
                assert isinstance(interaction.user, discord.Member)
                assert interaction.guild
                if interaction.user.voice is None:
                    await interaction.response.send_message("You are not connected to a voice channel.",
                                                            ephemeral=True)
                    return False
                if interaction.guild.voice_client is None:
                    await interaction.response.send_message("leave me alone")
                    return False
                if interaction.user.voice.channel == interaction.guild.voice_client.channel:
                    return True
                await interaction.response.send_message("You must be in same VC as Bot.", ephemeral=True)
                return False

            async def on_timeout(self) -> None:
                self.stop()
                if self.message is not None:
                    try:
                        await self.message.delete()
                    except discord.NotFound:
                        pass

            @staticmethod
            async def apply_filter():
                await vc.set_filter(wavelink.Filter(vc._filter, timescale=ts))

            @property
            def embed(self):
                embed = discord.Embed(title="Timescale Filters", colour=0xB7121F)
                embed.add_field(name="Speed", value=f"{round(ts.speed * 100)}%", inline=True)
                embed.add_field(name="Pitch", value=f"{round(ts.pitch * 100)}%", inline=True)
                embed.add_field(name="Rate", value=f"{round(ts.rate * 100)}%", inline=True)
                return embed

            @discord.ui.button(emoji="⬆", style=discord.ButtonStyle.success)
            async def up_speed(self, interaction: discord.Interaction, button: discord.Button):
                if round(ts.speed, 1) <= 1.9:
                    ts.speed += self.step
                button.disabled = True if (round(ts.speed, 1) >= 2.0) else False
                self.down_speed.disabled = False
                await self.apply_filter()
                await interaction.response.edit_message(embed=self.embed, view=self)

            @discord.ui.button(label="Speed", style=discord.ButtonStyle.primary, row=1)
            async def speed(self, interaction: discord.Interaction, button: discord.Button):
                ts.speed = 1.0
                self.up_speed.disabled = False
                self.down_speed.disabled = False
                await self.apply_filter()
                await interaction.response.edit_message(embed=self.embed, view=self)

            @discord.ui.button(emoji="⬇", style=discord.ButtonStyle.danger, row=2)
            async def down_speed(self, interaction: discord.Interaction, button: discord.Button):
                if round(ts.speed, 1) >= 0.6:
                    ts.speed -= self.step
                button.disabled = True if (round(ts.speed, 1) <= 0.5) else False
                self.up_speed.disabled = False
                await self.apply_filter()
                await interaction.response.edit_message(embed=self.embed, view=self)

            @discord.ui.button(emoji="⬆", style=discord.ButtonStyle.success)
            async def up_pitch(self, interaction: discord.Interaction, button: discord.Button):
                if round(ts.pitch, 1) <= 1.9:
                    ts.pitch += self.step
                button.disabled = True if (round(ts.pitch, 1) >= 2.0) else False
                self.down_pitch.disabled = False
                await self.apply_filter()
                await interaction.response.edit_message(embed=self.embed, view=self)

            @discord.ui.button(label="Pitch", style=discord.ButtonStyle.primary, row=1)
            async def pitch(self, interaction: discord.Interaction, button: discord.Button):
                ts.pitch = 1.0
                self.up_pitch.disabled = False
                self.down_pitch.disabled = False
                await self.apply_filter()
                await interaction.response.edit_message(embed=self.embed, view=self)

            @discord.ui.button(emoji="⬇", style=discord.ButtonStyle.danger, row=2)
            async def down_pitch(self, interaction: discord.Interaction, button: discord.Button):
                if round(ts.pitch, 1) >= 0.6:
                    ts.pitch -= self.step
                button.disabled = True if (round(ts.pitch, 1) <= 0.5) else False
                self.up_pitch.disabled = False
                await self.apply_filter()
                await interaction.response.edit_message(embed=self.embed, view=self)

            @discord.ui.button(emoji="⬆", style=discord.ButtonStyle.success)
            async def up_rate(self, interaction: discord.Interaction, button: discord.Button):
                if round(ts.rate, 1) <= 1.9:
                    ts.rate += self.step
                button.disabled = True if (round(ts.rate, 1) >= 2.0) else False
                self.down_rate.disabled = False
                await self.apply_filter()
                await interaction.response.edit_message(embed=self.embed, view=self)

            @discord.ui.button(label="Rate", style=discord.ButtonStyle.primary, row=1)
            async def rate(self, interaction: discord.Interaction, button: discord.Button):
                ts.rate = 1.0
                self.up_rate.disabled = False
                self.down_rate.disabled = False
                await self.apply_filter()
                await interaction.response.edit_message(embed=self.embed, view=self)

            @discord.ui.button(emoji="⬇", style=discord.ButtonStyle.danger, row=2)
            async def down_rate(self, interaction: discord.Interaction, button: discord.Button):
                if round(ts.rate, 1) >= 0.6:
                    ts.rate -= self.step
                button.disabled = True if (round(ts.rate, 1) <= 0.5) else False
                self.up_rate.disabled = False
                await self.apply_filter()
                await interaction.response.edit_message(embed=self.embed, view=self)

            @discord.ui.button(emoji="❎", label=f"10%", style=discord.ButtonStyle.gray, row=1)
            async def _step(self, interaction: discord.Interaction, button: discord.Button):
                if self.step == 0.1:
                    self.step = 0.05
                else:
                    self.step = 0.1
                button.label = f"{round(self.step * 100)}%"
                await interaction.response.edit_message(view=self)

        view = TimeScaleButtons()
        view.message = await ctx.send(embed=view.embed, view=view)

    @filters.command(name="reset", description="Reset all filters")
    async def reset(self, ctx: commands.Context):
        vc: wavelink.Player = ctx.voice_client  # type: ignore
        await vc.set_filter(wavelink.Filter())
        await ctx.send("Reset all filters.")


async def setup(bot: AssistantBot):
    await bot.add_cog(Filters(bot))
