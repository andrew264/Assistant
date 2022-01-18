import disnake
import lavalink
from disnake import ButtonStyle, Button, Interaction
from disnake.ext import commands


class Effects(commands.Cog):
    def __init__(self, client: disnake.Client):
        self.client = client
        self.client.lavalink = lavalink.Client(822454735310684230)
        self.client.lavalink.add_node('127.0.0.1', 2333, 'youshallnotpass', 'in', 'assistant-effects-node')

    # @commands.command()
    # async def reseteq(self, ctx: commands.Context):
    #    player: DefaultPlayer = self.client.lavalink.player_manager.get(ctx.guild.id)
    #    eq = [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (6, 0), (7, 0),
    #          (8, 0), (9, 0), (10, 0), (11, 0), (12, 0), (13, 0), (14, 0), ]
    #    _flat_eq = lavalink.filters.Equalizer()
    #    _flat_eq.update(bands=eq)
    #    await player.set_filter(_flat_eq)
    #    await ctx.send("Equalizer Reset")

    @commands.command(aliases=["filter"])
    async def filters(self, ctx: commands.Context):
        class FilterButtons(disnake.ui.View):
            def __init__(self, client):
                self.client = client
                self.message: disnake.Message
                super().__init__(timeout=30)

            async def on_timeout(self):
                try:
                    self.stop()
                    await self.message.delete()
                except disnake.errors.NotFound:
                    pass

            @disnake.ui.button(label="TimeScale", style=ButtonStyle.gray)
            async def timescale(self, button: Button, interaction: Interaction):
                await ctx.invoke(self.client.get_command("timescale"))
                button.disabled = True
                await interaction.response.edit_message(view=None)

        view = FilterButtons(self.client)
        view.message = await ctx.send("Available Filters", view=view)
        await ctx.message.delete(delay=30)

    class TimeScaleButtons(disnake.ui.View):

        def __init__(self, player):
            super().__init__(timeout=180)
            self.speed = 1.0
            self.pitch = 1.0
            self.rate = 1.0
            self.player: lavalink.DefaultPlayer = player
            self.message: disnake.Message

        async def on_timeout(self):
            try:
                self.stop()
                await self.message.delete()
            except disnake.errors.NotFound:
                pass

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
            await self.player.set_filter(time_filter)

        @property
        def embed(self):
            embed = disnake.Embed(title="Timescale Filters", colour=0xB7121F)
            embed.add_field(name="Speed\t", value=f"{round(self.speed * 100)}%", inline=True)
            embed.add_field(name="Pitch\t", value=f"{round(self.pitch * 100)}%", inline=True)
            embed.add_field(name="Rate\t", value=f"{round(self.rate * 100)}%", inline=True)
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

    @commands.command()
    async def timescale(self, ctx: commands.Context):
        player: lavalink.DefaultPlayer = self.client.lavalink.player_manager.get(ctx.guild.id)
        view = self.TimeScaleButtons(player)
        embed = disnake.Embed(title="Timescale Filters", colour=0xB7121F)
        embed.add_field(name="Speed", value="100%", inline=True)
        embed.add_field(name="Pitch", value="100%", inline=True)
        embed.add_field(name="Rate", value="100%", inline=True)
        view.message = await ctx.send(embed=embed, view=view)


def setup(client):
    client.add_cog(Effects(client))
