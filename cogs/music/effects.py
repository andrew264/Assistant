import asyncio

import disnake
import lavalink
from lavalink import DefaultPlayer as Player
from disnake import ButtonStyle, Button, Interaction
from disnake.ext import commands


class Effects(commands.Cog):
    def __init__(self, client: disnake.Client):
        self.client = client

    @commands.command(aliases=["filter"])
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

            @disnake.ui.button(label="ResetEQ", style=ButtonStyle.blurple)
            async def reseteq(self, button: Button, interaction: Interaction):
                eq = [(0, 0.0), (1, 0.0), (2, 0.0), (3, 0.0), (4, 0.0), (5, 0.0), (6, 0.0), (7, 0.0),
                      (8, 0.0), (9, 0.0), (10, 0.0), (11, 0.0), (12, 0.0), (13, 0.0), (14, 0.0), ]
                flat_eq = lavalink.filters.Equalizer()
                flat_eq.update(bands=eq)
                await player.set_filter(flat_eq)
                await interaction.response.edit_message(content="Equalizer set to flat.", view=None, )
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
        eq = lavalink.filters.Equalizer()

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


def setup(client):
    client.add_cog(Effects(client))
