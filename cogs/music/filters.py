from typing import Optional, cast

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
        vc: wavelink.Player = cast(wavelink.Player, ctx.voice_client)  # type: ignore
        # check if nightcore filter is already enabled
        filters: wavelink.Filters = vc.filters
        if filters.timescale.payload.get('rate', 1.) == 1.:
            filters.timescale.set(rate=1.3)
            await vc.set_filters(filters)
            await ctx.send("Enabled nightcore filter.")
            self.bot.logger.info(f"[FILTERS] Enabled nightcore filter in {ctx.guild}")
            return
        filters.timescale.set(rate=1.)
        await vc.set_filters(filters)
        await ctx.send("Disabled nightcore filter.")
        self.bot.logger.info(f"[FILTERS] Disabled nightcore filter in {ctx.guild}")

    @filters.command(name="vaporwave", aliases=['vw'], description="Enable/Disable vaporwave filter")
    async def vaporwave(self, ctx: commands.Context):
        vc: wavelink.Player = cast(wavelink.Player, ctx.voice_client)  # type: ignore
        # check if vaporwave filter is already enabled
        filters: wavelink.Filters = vc.filters
        if filters.tremolo.payload.get('depth', 0.) == 0.:
            filters.timescale.set(pitch=0.9)
            filters.tremolo.set(depth=0.3, frequency=14.0)
            filters.equalizer.set(bands=[{"band": 0, "gain": 0.3}, {"band": 1, "gain": 0.3}])
            await vc.set_filters(filters)
            await ctx.send("Enabled vaporwave filter.")
            self.bot.logger.info(f"[FILTERS] Enabled vaporwave filter in {ctx.guild}")
            return
        filters.timescale.reset()
        filters.tremolo.reset()
        filters.equalizer.reset()
        await vc.set_filters(filters)
        await ctx.send("Disabled vaporwave filter.")
        self.bot.logger.info(f"[FILTERS] Disabled vaporwave filter in {ctx.guild}")

    @filters.command(name="bass", aliases=['bb', 'bassboost'], description="Enable/Disable Bass-Boost filter")
    async def bass_boost(self, ctx: commands.Context):
        vc: wavelink.Player = cast(wavelink.Player, ctx.voice_client)  # type: ignore
        filters: wavelink.Filters = vc.filters

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

            @discord.ui.button(label="off", style=discord.ButtonStyle.gray)
            async def bass_off(self, interaction: discord.Interaction, button: discord.Button):
                filters.equalizer.set(bands=[{'band': 0, 'gain': 0.0}, {'band': 1, 'gain': 0.0}])
                await vc.set_filters(filters)
                embed = discord.Embed(title="Bass Boost Disabled", colour=0x000000)
                await interaction.response.edit_message(embed=embed, view=self)

            @discord.ui.button(label="low", style=discord.ButtonStyle.green)
            async def bass_low(self, interaction: discord.Interaction, button: discord.Button):
                filters.equalizer.set(bands=[{'band': 0, 'gain': 0.2}, {'band': 1, 'gain': 0.15}])
                await vc.set_filters(filters)
                embed = discord.Embed(title="Bass Boost set to Low", colour=0x00FF00)
                await interaction.response.edit_message(embed=embed, view=self)

            @discord.ui.button(label="medium", style=discord.ButtonStyle.blurple)
            async def bass_mid(self, interaction: discord.Interaction, button: discord.Button, ):
                filters.equalizer.set(bands=[{'band': 0, 'gain': 0.4}, {'band': 1, 'gain': 0.25}])
                await vc.set_filters(filters)
                embed = discord.Embed(title="Bass Boost set to Medium", colour=0x0000FF)
                await interaction.response.edit_message(embed=embed, view=self)

            @discord.ui.button(label="high", style=discord.ButtonStyle.danger)
            async def bass_hi(self, interaction: discord.Interaction, button: discord.Button, ):
                filters.equalizer.set(bands=[{'band': 0, 'gain': 0.6}, {'band': 1, 'gain': 0.35}])
                await vc.set_filters(filters)
                embed = discord.Embed(title="Bass Boost set to High", colour=0xFF0000)
                await interaction.response.edit_message(embed=embed, view=self)

        _embed = discord.Embed(title="Bass Boost", colour=0x000000)
        view = BassBoostButtons()
        view.message = await ctx.send(embed=_embed, view=view)

    @filters.command(name="treble", aliases=['tb', 'trebleboost'], description="Enable/Disable Treble-Boost filter")
    async def treble_boost(self, ctx: commands.Context):
        vc: wavelink.Player = cast(wavelink.Player, ctx.voice_client)  # type: ignore
        filters: wavelink.Filters = vc.filters

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

            @discord.ui.button(label="off", style=discord.ButtonStyle.gray)
            async def treble_off(self, interaction: discord.Interaction, button: discord.Button):
                filters.equalizer.set(bands=[{'band': 10, 'gain': 0.0},
                                             {'band': 11, 'gain': 0.0},
                                             {'band': 12, 'gain': 0.0},
                                             {'band': 13, 'gain': 0.0}])
                await vc.set_filters(filters)
                embed = discord.Embed(title="Treble Boost Disabled", colour=0x000000)
                await interaction.response.edit_message(embed=embed, view=self)

            @discord.ui.button(label="low", style=discord.ButtonStyle.green)
            async def treble_low(self, interaction: discord.Interaction, button: discord.Button):
                filters.equalizer.set(bands=[{'band': 10, 'gain': 0.2},
                                             {'band': 11, 'gain': 0.2},
                                             {'band': 12, 'gain': 0.2},
                                             {'band': 13, 'gain': 0.25}])
                await vc.set_filters(filters)
                embed = discord.Embed(title="Treble Boost set to Low", colour=0x00FF00)
                await interaction.response.edit_message(embed=embed, view=self)

            @discord.ui.button(label="medium", style=discord.ButtonStyle.blurple)
            async def treble_mid(self, interaction: discord.Interaction, button: discord.Button):
                filters.equalizer.set(bands=[{'band': 10, 'gain': 0.4},
                                             {'band': 11, 'gain': 0.4},
                                             {'band': 12, 'gain': 0.4},
                                             {'band': 13, 'gain': 0.45}])
                await vc.set_filters(filters)
                embed = discord.Embed(title="Treble Boost set to Medium", colour=0x0000FF)
                await interaction.response.edit_message(embed=embed, view=self)

            @discord.ui.button(label="high", style=discord.ButtonStyle.danger)
            async def treble_hi(self, interaction: discord.Interaction, button: discord.Button):
                filters.equalizer.set(bands=[{'band': 10, 'gain': 0.6},
                                             {'band': 11, 'gain': 0.6},
                                             {'band': 12, 'gain': 0.6},
                                             {'band': 13, 'gain': 0.65}])
                await vc.set_filters(filters)
                embed = discord.Embed(title="Treble Boost set to High", colour=0xFF0000)
                await interaction.response.edit_message(embed=embed, view=self)

        _embed = discord.Embed(title="Treble Boost", colour=0x000000)
        view = TrebleBoostButtons()
        view.message = await ctx.send(embed=_embed, view=view)

    @filters.command(name="8d", aliases=['surround', '3d'], description="Enable/Disable 8D filter")
    async def eight_d(self, ctx: commands.Context):
        vc: wavelink.Player = cast(wavelink.Player, ctx.voice_client)  # type: ignore
        # check if 8D filter is already enabled
        filters: wavelink.Filters = vc.filters
        if filters.rotation.payload.get('rotationHz', 0.0) == 0.0:
            filters.rotation.set(rotation_hz=0.2)
            await vc.set_filters(filters)
            await ctx.send("Enabled 8D filter.")
            self.bot.logger.info(f"[FILTERS] Enabled 8D filter in {ctx.guild}")
            return
        filters.rotation.reset()
        await vc.set_filters(filters)
        await ctx.send("Disabled 8D filter.")
        self.bot.logger.info(f"[FILTERS] Disabled 8D filter in {ctx.guild}")

    @filters.command(name="timescale", aliases=['ts', 'speed', 'pitch'], description="Enable/Disable timescale filter")
    async def timescale(self, ctx: commands.Context):
        vc: wavelink.Player = cast(wavelink.Player, ctx.voice_client)  # type: ignore
        filters: wavelink.Filters = vc.filters

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

            @property
            def embed(self):
                embed = discord.Embed(title="Timescale Filters", colour=0xB7121F)
                pload = filters.timescale.payload
                speed = round(pload.get('speed', 1.) * 100)
                pitch = round(pload.get('pitch', 1.) * 100)
                rate = round(pload.get('rate', 1.) * 100)
                embed.add_field(name="Speed", value=f"{speed}%", inline=True)
                embed.add_field(name="Pitch", value=f"{pitch}%", inline=True)
                embed.add_field(name="Rate", value=f"{rate}%", inline=True)
                return embed

            @discord.ui.button(emoji="⬆", style=discord.ButtonStyle.success)
            async def up_speed(self, interaction: discord.Interaction, button: discord.Button):
                speed = filters.timescale.payload.get('speed', 1.)
                if round(speed, 1) <= 1.9:
                    speed += self.step
                    filters.timescale.set(speed=speed)
                button.disabled = True if (round(speed, 1) >= 2.0) else False
                self.down_speed.disabled = False
                await vc.set_filters(filters)
                await interaction.response.edit_message(embed=self.embed, view=self)

            @discord.ui.button(label="Speed", style=discord.ButtonStyle.primary, row=1)
            async def speed(self, interaction: discord.Interaction, button: discord.Button):
                filters.timescale.set(speed=1.)
                self.up_speed.disabled = False
                self.down_speed.disabled = False
                await vc.set_filters(filters)
                await interaction.response.edit_message(embed=self.embed, view=self)

            @discord.ui.button(emoji="⬇", style=discord.ButtonStyle.danger, row=2)
            async def down_speed(self, interaction: discord.Interaction, button: discord.Button):
                speed = filters.timescale.payload.get('speed', 1.)
                if round(speed, 1) >= 0.6:
                    speed -= self.step
                    filters.timescale.set(speed=speed)
                button.disabled = True if (round(speed, 1) <= 0.5) else False
                self.up_speed.disabled = False
                await vc.set_filters(filters)
                await interaction.response.edit_message(embed=self.embed, view=self)

            @discord.ui.button(emoji="⬆", style=discord.ButtonStyle.success)
            async def up_pitch(self, interaction: discord.Interaction, button: discord.Button):
                pitch = filters.timescale.payload.get('pitch', 1.)
                if round(pitch, 1) <= 1.9:
                    pitch += self.step
                    filters.timescale.set(pitch=pitch)
                button.disabled = True if (round(pitch, 1) >= 2.0) else False
                self.down_pitch.disabled = False
                await vc.set_filters(filters)
                await interaction.response.edit_message(embed=self.embed, view=self)

            @discord.ui.button(label="Pitch", style=discord.ButtonStyle.primary, row=1)
            async def pitch(self, interaction: discord.Interaction, button: discord.Button):
                filters.timescale.set(pitch=1.)
                self.up_pitch.disabled = False
                self.down_pitch.disabled = False
                await vc.set_filters(filters)
                await interaction.response.edit_message(embed=self.embed, view=self)

            @discord.ui.button(emoji="⬇", style=discord.ButtonStyle.danger, row=2)
            async def down_pitch(self, interaction: discord.Interaction, button: discord.Button):
                pitch = filters.timescale.payload.get('pitch', 1.)
                if round(pitch, 1) >= 0.6:
                    pitch -= self.step
                    filters.timescale.set(pitch=pitch)
                button.disabled = True if (round(pitch, 1) <= 0.5) else False
                self.up_pitch.disabled = False
                await vc.set_filters(filters)
                await interaction.response.edit_message(embed=self.embed, view=self)

            @discord.ui.button(emoji="⬆", style=discord.ButtonStyle.success)
            async def up_rate(self, interaction: discord.Interaction, button: discord.Button):
                rate = filters.timescale.payload.get('rate', 1.)
                if round(rate, 1) <= 1.9:
                    rate += self.step
                    filters.timescale.set(rate=rate)
                button.disabled = True if (round(rate, 1) >= 2.0) else False
                self.down_rate.disabled = False
                await vc.set_filters(filters)
                await interaction.response.edit_message(embed=self.embed, view=self)

            @discord.ui.button(label="Rate", style=discord.ButtonStyle.primary, row=1)
            async def rate(self, interaction: discord.Interaction, button: discord.Button):
                filters.timescale.set(rate=1.)
                self.up_rate.disabled = False
                self.down_rate.disabled = False
                await vc.set_filters(filters)
                await interaction.response.edit_message(embed=self.embed, view=self)

            @discord.ui.button(emoji="⬇", style=discord.ButtonStyle.danger, row=2)
            async def down_rate(self, interaction: discord.Interaction, button: discord.Button):
                rate = filters.timescale.payload.get('rate', 1.)
                if round(rate, 1) >= 0.6:
                    rate -= self.step
                    filters.timescale.set(rate=rate)
                button.disabled = True if (round(rate, 1) <= 0.5) else False
                self.up_rate.disabled = False
                await vc.set_filters(filters)
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
        vc: wavelink.Player = cast(wavelink.Player, ctx.voice_client)  # type: ignore
        filters: wavelink.Filters = vc.filters
        filters.reset()
        await vc.set_filters(filters)
        await ctx.send("Reset all filters.")


async def setup(bot: AssistantBot):
    await bot.add_cog(Filters(bot))
