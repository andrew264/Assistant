import asyncio
from typing import Optional

import disnake
import lavalink
from disnake import ButtonStyle, Button, Interaction
from disnake.ext import commands
from lavalink import DefaultPlayer as Player


class Effects(commands.Cog):
    def __init__(self, client: disnake.Client):
        self.client = client

    @commands.command(aliases=["filter", "effects"])
    async def filters(self, ctx: commands.Context):
        player: Player = self.client.lavalink.player_manager.get(ctx.guild.id)

        class FilterButtons(disnake.ui.View):
            def __init__(self, client):
                self.client = client
                super().__init__(timeout=None)

            async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
                if interaction.author.voice is None:
                    await interaction.response.send_message("You are not connected to a voice channel.", ephemeral=True)
                    return False
                if interaction.author.voice.channel == interaction.guild.voice_client.channel:
                    return True
                await interaction.response.send_message("You must be in same VC as Bot.", ephemeral=True)
                return False

            @disnake.ui.button(label="TimeScale", style=ButtonStyle.gray)
            async def timescale(self, button: Button, interaction: Interaction):
                await ctx.invoke(self.client.get_command("timescale"))
                button.disabled = True
                await interaction.response.edit_message(view=None)
                await interaction.delete_original_message()

            @disnake.ui.button(label="BassBoost", style=ButtonStyle.gray)
            async def bassboost(self, button: Button, interaction: Interaction):
                await ctx.invoke(self.client.get_command("bassboost"))
                button.disabled = True
                await interaction.response.edit_message(view=None)
                await interaction.delete_original_message()

            @disnake.ui.button(label="TrebleBoost", style=ButtonStyle.gray)
            async def trebleboost(self, button: Button, interaction: Interaction):
                await ctx.invoke(self.client.get_command("trebleboost"))
                button.disabled = True
                await interaction.response.edit_message(view=None)
                await interaction.delete_original_message()

            @disnake.ui.button(label="ResetFilters", style=ButtonStyle.blurple)
            async def resetffilters(self, button: Button, interaction: Interaction):
                # remove all applied filters and effects
                for _filter in list(player.filters):
                    await player.remove_filter(_filter)
                await interaction.response.edit_message(content="Removed all Applied Filters", view=None, )
                await asyncio.sleep(5)
                await interaction.delete_original_message()

        view = FilterButtons(self.client)
        await ctx.send("Available Filters", view=view)
        await ctx.message.delete()

    @commands.command()
    async def timescale(self, ctx: commands.Context):
        player: Player = self.client.lavalink.player_manager.get(ctx.guild.id)

        class TimeScaleButtons(disnake.ui.View):
            def __init__(self):
                super().__init__(timeout=None)
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

            async def apply_filter(self):
                time_filter = lavalink.filters.Timescale()
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
                    self.speed += 0.1
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
                    self.speed -= 0.1
                button.disabled = True if (round(self.speed, 1) <= 0.5) else False
                self.up_speed.disabled = False
                await self.apply_filter()
                await interaction.response.edit_message(embed=self.embed, view=self)

            @disnake.ui.button(emoji="⬆", style=ButtonStyle.success)
            async def up_pitch(self, button: Button, interaction: Interaction):
                if round(self.pitch, 1) <= 1.9:
                    self.pitch += 0.1
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
                    self.pitch -= 0.1
                button.disabled = True if (round(self.pitch, 1) <= 0.5) else False
                self.up_pitch.disabled = False
                await self.apply_filter()
                await interaction.response.edit_message(embed=self.embed, view=self)

            @disnake.ui.button(emoji="⬆", style=ButtonStyle.success)
            async def up_rate(self, button: Button, interaction: Interaction):
                if round(self.rate, 1) <= 1.9:
                    self.rate += 0.1
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
                    self.rate -= 0.1
                button.disabled = True if (round(self.rate, 1) <= 0.5) else False
                self.up_rate.disabled = False
                await self.apply_filter()
                await interaction.response.edit_message(embed=self.embed, view=self)

        view = TimeScaleButtons()
        message = await ctx.send(embed=view.embed, view=view)
        try:
            await message.delete(delay=60)
        except disnake.NotFound:
            pass

    @commands.command(aliases=["bass"])
    async def bassboost(self, ctx: commands.Context):
        player: Player = self.client.lavalink.player_manager.get(ctx.guild.id)
        eq: Optional[lavalink.filters.Filter] = await player.get_filter("equalizer")

        class BassButtons(disnake.ui.View):
            def __init__(self):
                super().__init__(timeout=None)

            async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
                if interaction.author.voice is None:
                    await interaction.response.send_message("You are not connected to a voice channel.", ephemeral=True)
                    return False
                if interaction.author.voice.channel == interaction.guild.voice_client.channel:
                    return True
                await interaction.response.send_message("You must be in same VC as Bot.", ephemeral=True)
                return False

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
        message = await ctx.send(embed=embed0, view=view)
        try:
            await message.delete(delay=60)
        except disnake.NotFound:
            pass

    @commands.command(aliases=["treble"])
    async def trebleboost(self, ctx: commands.Context):
        player: Player = self.client.lavalink.player_manager.get(ctx.guild.id)
        eq: Optional[lavalink.filters.Filter] = await player.get_filter("equalizer")

        class TrebleButtons(disnake.ui.View):
            def __init__(self):
                super().__init__(timeout=None)

            async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
                if interaction.author.voice is None:
                    await interaction.response.send_message("You are not connected to a voice channel.", ephemeral=True)
                    return False
                if interaction.author.voice.channel == interaction.guild.voice_client.channel:
                    return True
                await interaction.response.send_message("You must be in same VC as Bot.", ephemeral=True)
                return False

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
        message = await ctx.send(embed=embed0, view=view)
        try:
            await message.delete(delay=60)
        except disnake.NotFound:
            pass

    @commands.command(aliases=["eq"])
    async def equalizer(self, ctx: commands.Context, *, bands: str):
        player: Player = self.client.lavalink.player_manager.get(ctx.guild.id)
        eq: Optional[lavalink.filters.Filter] = await player.get_filter("equalizer")
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
    async def karaoke(self, ctx: commands.Context, level: Optional[float], monolevel: Optional[float]
                      , filterband: Optional[float], filterwidth: Optional[float]):
        player: Player = self.client.lavalink.player_manager.get(ctx.guild.id)
        if not level and not monolevel and not filterband and not filterwidth:
            await player.remove_filter(lavalink.filters.Karaoke())
            await ctx.send("Karaoke disabled.")
            return
        karaoke = lavalink.filters.Karaoke()
        karaoke.update(level=level, monoLevel=monolevel, filterBand=filterband, filterWidth=filterwidth)
        await player.set_filter(karaoke)
        await ctx.send(
            f"Karaoke set to {level} level, {monolevel} mono level, {filterband} filter band, {filterwidth} filter width.")

    @commands.command()
    async def distort(self, ctx: commands.Context, sinOffset: Optional[float], sinScale: Optional[float],
                      cosOffset: Optional[float], cosScale: Optional[float], tanOffset: Optional[float]
                      , tanScale: Optional[float], offset: Optional[float], scale: Optional[float]):
        player: Player = self.client.lavalink.player_manager.get(ctx.guild.id)
        if (not sinOffset and not sinScale
                and not cosOffset and not cosScale
                and not tanOffset and not tanScale
                and not offset and not scale):
            await player.remove_filter(lavalink.filters.Distortion())
            await ctx.send("Distortion disabled.")
            return
        player: Player = self.client.lavalink.player_manager.get(ctx.guild.id)
        distort = lavalink.filters.Distortion()
        distort.update(sinOffset=sinOffset, sinScale=sinScale, cosOffset=cosOffset, cosScale=cosScale,
                       tanOffset=tanOffset, tanScale=tanScale, offset=offset, scale=scale)
        await player.set_filter(distort)
        await ctx.send(f"Distortion Updated.")


def setup(client):
    client.add_cog(Effects(client))
