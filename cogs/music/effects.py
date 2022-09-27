from typing import Optional

import disnake
import lavalink
from disnake import ButtonStyle, Button, Interaction
from disnake.ext import commands
from lavalink import DefaultPlayer as Player

import assistant


class Effects(commands.Cog):
    def __init__(self, client: assistant.Client):
        self.client = client

    @commands.command(aliases=["filter", "effects"])
    async def filters(self, ctx: commands.Context):
        player: Player = self.client.lavalink.player_manager.get(ctx.guild.id)

        class FilterButtons(disnake.ui.View):
            def __init__(self, client):
                self.client = client
                self.message: Optional[disnake.Message] = None
                super().__init__(timeout=90)

            async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
                if interaction.author.voice is None:
                    await interaction.response.send_message("You are not connected to a voice channel.", ephemeral=True)
                    return False
                if interaction.author.voice.channel == interaction.guild.voice_client.channel:
                    return True
                await interaction.response.send_message("You must be in same VC as Bot.", ephemeral=True)
                return False

            async def on_timeout(self) -> None:
                try:
                    await self.message.delete()
                except (disnake.HTTPException, disnake.NotFound):
                    pass

            @staticmethod
            async def _reset_filters():
                # remove all applied filters and effects and apply flat EQ
                for _filter in list(player.filters):
                    if _filter.lower() == "volume":
                        continue
                    await player.remove_filter(_filter)
                flat_eq = lavalink.Equalizer()
                flat_eq.update(bands=[(band, 0.0) for band in range(0, 15)])
                await player.set_filter(flat_eq)

            @disnake.ui.button(label="TimeScale", style=ButtonStyle.gray)
            async def timescale(self, button: Button, interaction: Interaction):
                await ctx.invoke(self.client.get_command("timescale"))
                button.disabled = True
                await interaction.response.edit_message(view=self)

            @disnake.ui.button(label="BassBoost", style=ButtonStyle.gray)
            async def bass_boost(self, button: Button, interaction: Interaction):
                await ctx.invoke(self.client.get_command("bassboost"))
                button.disabled = True
                await interaction.response.edit_message(view=self)

            @disnake.ui.button(label="TrebleBoost", style=ButtonStyle.gray)
            async def treble_boost(self, button: Button, interaction: Interaction):
                await ctx.invoke(self.client.get_command("trebleboost"))
                button.disabled = True
                await interaction.response.edit_message(view=self)

            @disnake.ui.button(label="NightCore", style=ButtonStyle.blurple, row=1)
            async def nightcore(self, button: Button, interaction: Interaction):
                await self._reset_filters()
                nc = lavalink.Timescale()
                nc.update(speed=1.29999, pitch=1.29999, rate=1.0)
                await player.set_filter(nc)
                await interaction.response.edit_message(content="Nightcore Enabled", view=self)
                self.client.logger.info(f"{interaction.author} enabled Nightcore")

            @disnake.ui.button(label="VapourWave", style=ButtonStyle.blurple, row=1)
            async def vapour_wave(self, button: Button, interaction: Interaction):
                await self._reset_filters()
                eq = lavalink.Equalizer()
                eq.update(bands=[(0, 0.3), (1, 0.3)])
                pitch = lavalink.Timescale()
                pitch.update(pitch=0.5)
                tremolo = lavalink.Tremolo()
                tremolo.update(depth=0.3, frequency=14)
                await player.set_filter(eq)
                await player.set_filter(pitch)
                await player.set_filter(tremolo)
                await interaction.response.edit_message(content="VapourWave Enabled", view=self)
                self.client.logger.info(f"{interaction.author} enabled VapourWave")

            @disnake.ui.button(label="8D", style=ButtonStyle.blurple, row=1)
            async def eight_d(self, button: Button, interaction: Interaction):
                await self._reset_filters()
                rotate = lavalink.Rotation()
                rotate.update(rotationHz=0.2)
                await player.set_filter(rotate)
                await interaction.response.edit_message(content="8D Surround Enabled", view=self)
                self.client.logger.info(f"{interaction.author} enabled 8D Surround")

            @disnake.ui.button(label="ResetFilters", style=ButtonStyle.danger, row=2)
            async def reset_filters(self, button: Button, interaction: Interaction):
                await self._reset_filters()
                await interaction.response.edit_message(content="Removed all Applied Filters", view=None, )
                self.client.logger.info(f"{interaction.author} removed all applied filters")
                self.timeout = 15

        view = FilterButtons(self.client)
        view.message = await ctx.send("Available Filters", view=view)
        await ctx.message.delete()

    @commands.command()
    async def timescale(self, ctx: commands.Context):
        player: Player = self.client.lavalink.player_manager.get(ctx.guild.id)
        time_filter = lavalink.filters.Timescale()

        class TimeScaleButtons(disnake.ui.View):
            def __init__(self):
                super().__init__(timeout=120)
                self.step = 0.1
                self.message: Optional[disnake.Message] = None
                if 'timescale' in player.filters:
                    timescale: dict = player.filters['timescale'].values
                    self.speed = timescale["speed"]
                    self.pitch = timescale["pitch"]
                    self.rate = timescale["rate"]
                else:
                    self.speed = 1.0
                    self.pitch = 1.0
                    self.rate = 1.0

            async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
                if interaction.author.voice is None:
                    await interaction.response.send_message("You are not connected to a voice channel.", ephemeral=True)
                    return False
                if interaction.author.voice.channel == interaction.guild.voice_client.channel:
                    return True
                await interaction.response.send_message("You must be in same VC as Bot.", ephemeral=True)
                return False

            async def on_timeout(self) -> None:
                try:
                    await self.message.delete()
                except (disnake.HTTPException, disnake.NotFound):
                    pass

            async def apply_filter(self):
                time_filter.update(speed=self.speed, pitch=self.pitch, rate=self.rate)
                await player.set_filter(time_filter)

            @property
            def embed(self):
                embed = disnake.Embed(title="Timescale Filters", colour=0xB7121F)
                embed.add_field(name="Speed", value=f"{round(self.speed * 100)}%", inline=True)
                embed.add_field(name="Pitch", value=f"{round(self.pitch * 100)}%", inline=True)
                embed.add_field(name="Rate", value=f"{round(self.rate * 100)}%", inline=True)
                return embed

            @disnake.ui.button(emoji="⬆", style=ButtonStyle.success)
            async def up_speed(self, button: Button, interaction: Interaction):
                if round(self.speed, 1) <= 1.9:
                    self.speed += self.step
                button.disabled = True if (round(self.speed, 1) >= 2.0) else False
                self.down_speed.disabled = False
                await self.apply_filter()
                await interaction.response.edit_message(embed=self.embed, view=self)

            @disnake.ui.button(label="Speed", style=ButtonStyle.primary, row=1)
            async def speed(self, button: Button, interaction: Interaction):
                self.speed = 1.0
                self.up_speed.disabled = False
                self.down_speed.disabled = False
                await self.apply_filter()
                await interaction.response.edit_message(embed=self.embed, view=self)

            @disnake.ui.button(emoji="⬇", style=ButtonStyle.danger, row=2)
            async def down_speed(self, button: Button, interaction: Interaction):
                if round(self.speed, 1) >= 0.6:
                    self.speed -= self.step
                button.disabled = True if (round(self.speed, 1) <= 0.5) else False
                self.up_speed.disabled = False
                await self.apply_filter()
                await interaction.response.edit_message(embed=self.embed, view=self)

            @disnake.ui.button(emoji="⬆", style=ButtonStyle.success)
            async def up_pitch(self, button: Button, interaction: Interaction):
                if round(self.pitch, 1) <= 1.9:
                    self.pitch += self.step
                button.disabled = True if (round(self.pitch, 1) >= 2.0) else False
                self.down_pitch.disabled = False
                await self.apply_filter()
                await interaction.response.edit_message(embed=self.embed, view=self)

            @disnake.ui.button(label="Pitch", style=ButtonStyle.primary, row=1)
            async def pitch(self, button: Button, interaction: Interaction):
                self.pitch = 1.0
                self.up_pitch.disabled = False
                self.down_pitch.disabled = False
                await self.apply_filter()
                await interaction.response.edit_message(embed=self.embed, view=self)

            @disnake.ui.button(emoji="⬇", style=ButtonStyle.danger, row=2)
            async def down_pitch(self, button: Button, interaction: Interaction):
                if round(self.pitch, 1) >= 0.6:
                    self.pitch -= self.step
                button.disabled = True if (round(self.pitch, 1) <= 0.5) else False
                self.up_pitch.disabled = False
                await self.apply_filter()
                await interaction.response.edit_message(embed=self.embed, view=self)

            @disnake.ui.button(emoji="⬆", style=ButtonStyle.success)
            async def up_rate(self, button: Button, interaction: Interaction):
                if round(self.rate, 1) <= 1.9:
                    self.rate += self.step
                button.disabled = True if (round(self.rate, 1) >= 2.0) else False
                self.down_rate.disabled = False
                await self.apply_filter()
                await interaction.response.edit_message(embed=self.embed, view=self)

            @disnake.ui.button(label="Rate", style=ButtonStyle.primary, row=1)
            async def rate(self, button: Button, interaction: Interaction):
                self.rate = 1.0
                self.up_rate.disabled = False
                self.down_rate.disabled = False
                await self.apply_filter()
                await interaction.response.edit_message(embed=self.embed, view=self)

            @disnake.ui.button(emoji="⬇", style=ButtonStyle.danger, row=2)
            async def down_rate(self, button: Button, interaction: Interaction):
                if round(self.rate, 1) >= 0.6:
                    self.rate -= self.step
                button.disabled = True if (round(self.rate, 1) <= 0.5) else False
                self.up_rate.disabled = False
                await self.apply_filter()
                await interaction.response.edit_message(embed=self.embed, view=self)

            @disnake.ui.button(emoji="❎", label=f"10%", style=ButtonStyle.gray, row=1)
            async def step(self, button: Button, interaction: Interaction):
                if self.step == 0.1:
                    self.step = 0.05
                else:
                    self.step = 0.1
                button.label = f"{round(self.step * 100)}%"
                await interaction.response.edit_message(view=self)

        view = TimeScaleButtons()
        view.message = await ctx.send(embed=view.embed, view=view)

    @commands.command(aliases=["bass"])
    async def bassboost(self, ctx: commands.Context):
        player: Player = self.client.lavalink.player_manager.get(ctx.guild.id)
        eq: Optional[lavalink.filters.Filter] = player.filters.get("equalizer")

        class BassButtons(disnake.ui.View):
            def __init__(self):
                super().__init__(timeout=90)
                self.message: Optional[disnake.Message] = None

            async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
                if interaction.author.voice is None:
                    await interaction.response.send_message("You are not connected to a voice channel.", ephemeral=True)
                    return False
                if interaction.author.voice.channel == interaction.guild.voice_client.channel:
                    return True
                await interaction.response.send_message("You must be in same VC as Bot.", ephemeral=True)
                return False

            async def on_timeout(self) -> None:
                try:
                    await self.message.delete()
                except (disnake.HTTPException, disnake.NotFound):
                    pass

            @disnake.ui.button(label="off", style=ButtonStyle.gray)
            async def bass_off(self, button: Button, interaction: Interaction):
                eq.update(bands=[(0, 0.0), (1, 0.0)])
                await player.set_filter(eq)
                embed = disnake.Embed(title="Bass Boost Disabled", colour=0x000000)
                await interaction.response.edit_message(embed=embed, view=self)

            @disnake.ui.button(label="low", style=ButtonStyle.green)
            async def bass_low(self, button: Button, interaction: Interaction):
                eq.update(bands=[(0, 0.2), (1, 0.15)])
                await player.set_filter(eq)
                embed = disnake.Embed(title="Bass Boost set to Low", colour=0x00FF00)
                await interaction.response.edit_message(embed=embed, view=self)

            @disnake.ui.button(label="medium", style=ButtonStyle.blurple)
            async def bass_mid(self, button: Button, interaction: Interaction):
                eq.update(bands=[(0, 0.4), (1, 0.25)])
                await player.set_filter(eq)
                embed = disnake.Embed(title="Bass Boost set to Medium", colour=0x0000FF)
                await interaction.response.edit_message(embed=embed, view=self)

            @disnake.ui.button(label="high", style=ButtonStyle.danger)
            async def bass_hi(self, button: Button, interaction: Interaction):
                eq.update(bands=[(0, 0.6), (1, 0.4)])
                await player.set_filter(eq)
                embed = disnake.Embed(title="Bass Boost set to High", colour=0xFF0000)
                await interaction.response.edit_message(embed=embed, view=self)

        view = BassButtons()
        embed0 = disnake.Embed(title="Bass Boost Disabled", colour=0x000000)
        view.message = await ctx.send(embed=embed0, view=view)

    @commands.command(aliases=["treble"])
    async def trebleboost(self, ctx: commands.Context):
        player: Player = self.client.lavalink.player_manager.get(ctx.guild.id)
        eq: Optional[lavalink.filters.Filter] = player.filters.get("equalizer")

        class TrebleButtons(disnake.ui.View):
            def __init__(self):
                super().__init__(timeout=90)
                self.message: Optional[disnake.Message] = None

            async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
                if interaction.author.voice is None:
                    await interaction.response.send_message("You are not connected to a voice channel.", ephemeral=True)
                    return False
                if interaction.author.voice.channel == interaction.guild.voice_client.channel:
                    return True
                await interaction.response.send_message("You must be in same VC as Bot.", ephemeral=True)
                return False

            async def on_timeout(self) -> None:
                try:
                    await self.message.delete()
                except (disnake.HTTPException, disnake.NotFound):
                    pass

            @disnake.ui.button(label="off", style=ButtonStyle.gray)
            async def treble_off(self, button: Button, interaction: Interaction):
                eq.update(bands=[(10, 0.0), (11, 0.0), (12, 0.0), (13, 0.0)])
                await player.set_filter(eq)
                embed = disnake.Embed(title="Treble Boost Disabled", colour=0x000000)
                await interaction.response.edit_message(embed=embed, view=self)

            @disnake.ui.button(label="low", style=ButtonStyle.green)
            async def treble_low(self, button: Button, interaction: Interaction):
                eq.update(bands=[(10, 0.2), (11, 0.2), (12, 0.2), (13, 0.25)])
                await player.set_filter(eq)
                embed = disnake.Embed(title="Treble Boost set to Low", colour=0x00FF00)
                await interaction.response.edit_message(embed=embed, view=self)

            @disnake.ui.button(label="medium", style=ButtonStyle.blurple)
            async def treble_mid(self, button: Button, interaction: Interaction):
                eq.update(bands=[(10, 0.4), (11, 0.4), (12, 0.4), (13, 0.45)])
                await player.set_filter(eq)
                embed = disnake.Embed(title="Treble Boost set to Medium", colour=0x0000FF)
                await interaction.response.edit_message(embed=embed, view=self)

            @disnake.ui.button(label="high", style=ButtonStyle.danger)
            async def treble_hi(self, button: Button, interaction: Interaction):
                eq.update(bands=[(10, 0.6), (11, 0.6), (12, 0.6), (13, 0.65)])
                await player.set_filter(eq)
                embed = disnake.Embed(title="Treble Boost set to High", colour=0xFF0000)
                await interaction.response.edit_message(embed=embed, view=self)

        view = TrebleButtons()
        embed0 = disnake.Embed(title="Treble Boost Disabled", colour=0x000000)
        view.message = await ctx.send(embed=embed0, view=view)

    @commands.command(aliases=["eq"])
    async def equalizer(self, ctx: commands.Context, *, bands: str):
        player: Player = self.client.lavalink.player_manager.get(ctx.guild.id)
        eq: Optional[lavalink.filters.Filter] = player.filters.get("equalizer")
        bands = bands.split(",")
        bands = [float(band) for band in bands]
        bands = [(int(i), band) for i, band in enumerate(bands)]
        eq.update(bands=bands)
        await player.set_filter(eq)

    @commands.command()
    async def rotation(self, ctx: commands.Context, hertz: Optional[float]):
        player: Player = self.client.lavalink.player_manager.get(ctx.guild.id)
        if hertz is None:
            await player.remove_filter(lavalink.filters.Rotation())
            await ctx.send("Rotation disabled.")
            return
        if hertz < 0:
            await ctx.send("Rotation must be bigger than or equal to 0")
            return
        rotation = lavalink.filters.Rotation()
        rotation.update(rotationHz=hertz)
        await player.set_filter(rotation)
        await ctx.send(f"Rotation set to {hertz} Hz.")

    @commands.command()
    async def vibrato(self, ctx: commands.Context, freq: Optional[float], depth: Optional[float]):
        player: Player = self.client.lavalink.player_manager.get(ctx.guild.id)
        if not freq and not depth:
            await player.remove_filter(lavalink.filters.Vibrato())
            await ctx.send("Vibrato disabled.")
            return
        if not 0 < freq <= 14:
            await ctx.send("Frequency must be bigger than 0, and less than or equal to 14")
        if not 0 < depth <= 1:
            await ctx.send("Depth must be bigger than 0, and less than or equal to 1.")
        vibrato = lavalink.filters.Vibrato()
        vibrato.update(frequency=freq, depth=depth)
        await player.set_filter(vibrato)
        await ctx.send(f"Vibrato set to {freq} Hz, {depth} depth.")

    @commands.command()
    async def tremlo(self, ctx: commands.Context, hertz: Optional[float], depth: Optional[float]):
        player: Player = self.client.lavalink.player_manager.get(ctx.guild.id)
        if not hertz and not depth:
            await player.remove_filter(lavalink.filters.Tremolo())
            await ctx.send("Tremolo disabled.")
            return
        if not 0 < hertz:
            await ctx.send("Frequency must be bigger than 0.")
        if not 0 < depth <= 1:
            await ctx.send("Depth must be bigger than 0, and less than or equal to 1.")
        tremolo = lavalink.filters.Tremolo()
        tremolo.update(frequency=hertz, depth=depth)
        await player.set_filter(tremolo)
        await ctx.send(f"Tremolo set to {hertz} Hz, {depth} depth.")

    @commands.command()
    async def karaoke(self, ctx: commands.Context, level: Optional[float], monolevel: Optional[float],
                      filterband: Optional[float], filterwidth: Optional[float]):
        player: Player = self.client.lavalink.player_manager.get(ctx.guild.id)
        if not level and not monolevel and not filterband and not filterwidth:
            await player.remove_filter(lavalink.filters.Karaoke())
            await ctx.send("Karaoke disabled.")
            return
        karaoke = lavalink.filters.Karaoke()
        karaoke.update(level=level, monoLevel=monolevel, filterBand=filterband, filterWidth=filterwidth)
        await player.set_filter(karaoke)
        await ctx.send(f"Karaoke set to {level} level, {monolevel} mono level, " +
                       f"{filterband} filter band, {filterwidth} filter width.")

    @commands.command()
    async def distort(self, ctx: commands.Context, sin_offset: Optional[float], sin_scale: Optional[float],
                      cos_offset: Optional[float], cos_scale: Optional[float], tan_offset: Optional[float],
                      tan_scale: Optional[float], offset: Optional[float], scale: Optional[float]):
        player: Player = self.client.lavalink.player_manager.get(ctx.guild.id)
        if (not sin_offset and not sin_scale
                and not cos_offset and not cos_scale
                and not tan_offset and not tan_scale
                and not offset and not scale):
            await player.remove_filter(lavalink.filters.Distortion())
            await ctx.send("Distortion disabled.")
            return
        player: Player = self.client.lavalink.player_manager.get(ctx.guild.id)
        distort = lavalink.filters.Distortion()
        distort.update(sinOffset=sin_offset, sinScale=sin_scale, cosOffset=cos_offset, cosScale=cos_scale,
                       tanOffset=tan_offset, tanScale=tan_scale, offset=offset, scale=scale)
        await player.set_filter(distort)
        await ctx.send(f"Distortion Updated.")


def setup(client):
    client.add_cog(Effects(client))
