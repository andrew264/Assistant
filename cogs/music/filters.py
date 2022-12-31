# Imports
import typing

import disnake
import lavalink
from disnake import ButtonStyle, Button, Interaction
from disnake.ext import commands
from lavalink import DefaultPlayer as Player

from assistant import Client
from config import LavalinkConfig


class MusicFilters(commands.Cog):
    def __init__(self, client: Client):
        self.client = client
        self.logger = client.logger

    async def _reset_filters(self, guild_id: int) -> None:
        # remove all applied filters and effects and apply flat EQ
        player: Player = self.client.lavalink.player_manager.get(guild_id)
        for _filter in list(player.filters):
            if _filter.lower() == "volume":
                continue
            await player.remove_filter(_filter)
        flat_eq = lavalink.Equalizer()
        flat_eq.update(bands=[(band, 0.0) for band in range(0, 15)])
        await player.set_filter(flat_eq)

    @commands.slash_command(name="filter", description="Apply filters to the music")
    async def filters(self, inter: disnake.ApplicationCommandInteraction) -> None:
        if self.client.lavalink is None:
            await inter.response.send_message("Music Player is not connected.", ephemeral=True)
            return

    @filters.sub_command(name="bass-boost", description="Apply bass boost filter to the music")
    async def bass_boost(self, inter: disnake.ApplicationCommandInteraction) -> None:
        player: Player = self.client.lavalink.player_manager.get(inter.guild.id)

        class BassBoostButtons(disnake.ui.View):
            def __init__(self):
                super().__init__(timeout=180)

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
                    await inter.edit_original_message(view=None)
                except disnake.NotFound:
                    pass

            @staticmethod
            async def _update_eq(bands: list) -> None:
                # update the EQ filter
                eq: typing.Optional[lavalink.filters.Filter] = player.filters.get("equalizer")
                eq.update(bands=bands)
                await player.set_filter(eq)

            @disnake.ui.button(label="off", style=ButtonStyle.gray)
            async def bass_off(self, button: Button, interaction: Interaction):
                await self._update_eq([(0, 0.0), (1, 0.0)])
                embed = disnake.Embed(title="Bass Boost Disabled", colour=0x000000)
                await interaction.response.edit_message(embed=embed, view=self)

            @disnake.ui.button(label="low", style=ButtonStyle.green)
            async def bass_low(self, button: Button, interaction: Interaction):
                await self._update_eq([(0, 0.2), (1, 0.15)])
                embed = disnake.Embed(title="Bass Boost set to Low", colour=0x00FF00)
                await interaction.response.edit_message(embed=embed, view=self)

            @disnake.ui.button(label="medium", style=ButtonStyle.blurple)
            async def bass_mid(self, button: Button, interaction: Interaction):
                await self._update_eq([(0, 0.4), (1, 0.25)])
                embed = disnake.Embed(title="Bass Boost set to Medium", colour=0x0000FF)
                await interaction.response.edit_message(embed=embed, view=self)

            @disnake.ui.button(label="high", style=ButtonStyle.danger)
            async def bass_hi(self, button: Button, interaction: Interaction):
                await self._update_eq([(0, 0.6), (1, 0.4)])
                embed = disnake.Embed(title="Bass Boost set to High", colour=0xFF0000)
                await interaction.response.edit_message(embed=embed, view=self)

        embed0 = disnake.Embed(title="Bass Boost Disabled", colour=0x000000)
        await inter.response.send_message(embed=embed0, view=BassBoostButtons())
        self.logger.info(f"{inter.author} used bass boost command in {inter.guild}")

    @filters.sub_command(name="treble-boost", description="Apply treble boost filter to the music")
    async def treble_boost(self, inter: disnake.ApplicationCommandInteraction) -> None:
        player: Player = self.client.lavalink.player_manager.get(inter.guild.id)

        class TrebleBoostButtons(disnake.ui.View):
            def __init__(self):
                super().__init__(timeout=180)

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
                    await inter.edit_original_message(view=None)
                except disnake.NotFound:
                    pass

            @staticmethod
            async def _update_eq(bands: list) -> None:
                # update the EQ filter
                eq: typing.Optional[lavalink.filters.Filter] = player.filters.get("equalizer")
                eq.update(bands=bands)
                await player.set_filter(eq)

            @disnake.ui.button(label="off", style=ButtonStyle.gray)
            async def treble_off(self, button: Button, interaction: Interaction):
                await self._update_eq([(10, 0.0), (11, 0.0), (12, 0.0), (13, 0.0)])
                embed = disnake.Embed(title="Treble Boost Disabled", colour=0x000000)
                await interaction.response.edit_message(embed=embed, view=self)

            @disnake.ui.button(label="low", style=ButtonStyle.green)
            async def treble_low(self, button: Button, interaction: Interaction):
                await self._update_eq([(10, 0.2), (11, 0.2), (12, 0.2), (13, 0.25)])
                embed = disnake.Embed(title="Treble Boost set to Low", colour=0x00FF00)
                await interaction.response.edit_message(embed=embed, view=self)

            @disnake.ui.button(label="medium", style=ButtonStyle.blurple)
            async def treble_mid(self, button: Button, interaction: Interaction):
                await self._update_eq([(10, 0.4), (11, 0.4), (12, 0.4), (13, 0.45)])
                embed = disnake.Embed(title="Treble Boost set to Medium", colour=0x0000FF)
                await interaction.response.edit_message(embed=embed, view=self)

            @disnake.ui.button(label="high", style=ButtonStyle.danger)
            async def treble_hi(self, button: Button, interaction: Interaction):
                await self._update_eq([(10, 0.6), (11, 0.6), (12, 0.6), (13, 0.65)])
                embed = disnake.Embed(title="Treble Boost set to High", colour=0xFF0000)
                await interaction.response.edit_message(embed=embed, view=self)

        embed0 = disnake.Embed(title="Treble Boost Disabled", colour=0x000000)
        await inter.response.send_message(embed=embed0, view=TrebleBoostButtons())
        self.logger.info(f"{inter.author} used treble-boost command in {inter.guild}")

    @filters.sub_command(name="time-scale", description="Apply time scale filter to the music")
    async def time_scale(self, inter: disnake.ApplicationCommandInteraction) -> None:
        player: Player = self.client.lavalink.player_manager.get(inter.guild.id)
        time_filter = lavalink.filters.Timescale()

        class TimeScaleButtons(disnake.ui.View):
            def __init__(self):
                super().__init__(timeout=180)
                self.step: float = 0.1
                self.speed: float = 1.0
                self.pitch: float = 1.0
                self.rate: float = 1.0
                self._update_values()

            def _update_values(self):
                if 'timescale' in player.filters:
                    timescale: dict = player.filters['timescale'].values
                    self.speed = float(timescale["speed"])
                    self.pitch = float(timescale["pitch"])
                    self.rate = float(timescale["rate"])

            async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
                if interaction.author.voice is None:
                    await interaction.response.send_message("You are not connected to a voice channel.",
                                                            ephemeral=True)
                    return False
                if interaction.author.voice.channel == interaction.guild.voice_client.channel:
                    self._update_values()
                    return True
                await interaction.response.send_message("You must be in same VC as Bot.", ephemeral=True)
                return False

            async def on_timeout(self) -> None:
                try:
                    await inter.edit_original_message(view=None)
                except disnake.NotFound:
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
        await inter.response.send_message(embed=view.embed, view=view)
        self.logger.info(f"Timescale Filters started by {inter.author} in {inter.guild}")

    @filters.sub_command(name="nightcore", description="Apply Nightcore Filter")
    async def nightcore(self, inter: disnake.ApplicationCommandInteraction):
        player: Player = self.client.lavalink.player_manager.get(inter.guild_id)
        if "timescale" in player.filters:
            await player.remove_filter("timescale")
            await inter.response.send_message(content="Nightcore Disabled")
            self.logger.info(f"{inter.author} disabled Nightcore Filter in {inter.guild}")
        else:
            nc = lavalink.Timescale()
            nc.update(speed=1.29999, pitch=1.29999, rate=1.0)
            await player.set_filter(nc)
            await inter.response.send_message(content="Nightcore Enabled")
            self.logger.info(f"{inter.author} enabled Nightcore Filter in {inter.guild}")

    @filters.sub_command(name="vaporwave", description="Apply VaporWave Filter")
    async def vapor_wave(self, inter: disnake.ApplicationCommandInteraction):
        player: Player = self.client.lavalink.player_manager.get(inter.guild_id)
        eq: lavalink.Equalizer = player.get_filter("equalizer")
        if "tremolo" in player.filters:
            eq.update(bands=[(0, 0.0), (1, 0.0)])
            await player.set_filter(eq)
            await player.remove_filter("timescale")
            await player.remove_filter("tremolo")
            await inter.response.send_message(content="VaporWave Disabled")
            self.logger.info(f"{inter.author} disabled VaporWave Filter in {inter.guild}")
        else:
            eq.update(bands=[(0, 0.3), (1, 0.3)])
            pitch = lavalink.Timescale()
            pitch.update(pitch=0.5)
            tremolo = lavalink.Tremolo()
            tremolo.update(depth=0.3, frequency=14)
            await player.set_filter(eq)
            await player.set_filter(pitch)
            await player.set_filter(tremolo)
            await inter.response.send_message(content="VaporWave Enabled")
            self.logger.info(f"{inter.author} enabled VaporWave Filter in {inter.guild}")

    @filters.sub_command(name="surround-audio", description="Apply 8D Audio Filter")
    async def eight_d(self, inter: disnake.ApplicationCommandInteraction):
        player: Player = self.client.lavalink.player_manager.get(inter.guild_id)
        if "rotation" in player.filters:
            await player.remove_filter("rotation")
            await inter.response.send_message(content="8D Audio Disabled")
            self.logger.info(f"{inter.author} disabled 8D Audio Filter in {inter.guild}")
        else:
            rotate = lavalink.Rotation()
            rotate.update(rotationHz=0.2)
            await player.set_filter(rotate)
            await inter.response.send_message(content="Surround Audio Enabled")
            self.logger.info(f"{inter.author} enabled Surround Audio Filter in {inter.guild}")

    @filters.sub_command(name="reset", description="Remove all applied Filters")
    async def reset(self, inter: disnake.ApplicationCommandInteraction):
        await self._reset_filters(inter.guild_id)
        await inter.response.send_message(content="Filters Reset")
        self.logger.info(f"{inter.author} reset Filters in {inter.guild}")

    @filters.before_invoke
    async def ensure_voice(self, inter: disnake.ApplicationCommandInteraction) -> None:
        if not inter.author.voice or not inter.author.voice.channel:
            raise commands.CheckFailure("You are not connected to a VC.")

        player: Player = self.client.lavalink.player_manager.get(inter.guild.id)
        if player is None or not player.is_connected:
            raise commands.CheckFailure("Bot is not connected to a VC.")

        if inter.guild.me.voice and inter.guild.me.voice.channel != inter.author.voice.channel:
            raise commands.CheckFailure("You must be in same VC as Bot.")


def setup(client):
    config = LavalinkConfig()
    if not config:
        client.logger.warning("Lavalink Config not found. Music Filters will not be loaded.")
        return
    client.add_cog(MusicFilters(client))
