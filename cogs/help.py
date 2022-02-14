# Import
import disnake
from disnake import (
    Colour,
    Embed,
)
from disnake.ext import commands
from disnake.ui import View, button


class HelpMe(commands.Cog):
    def __init__(self, client: disnake.Client):
        self.client = client

    class HelpButtons(View):
        def __init__(self):
            super().__init__(timeout=60.0)
            self.inter: disnake.ApplicationCommandInteraction

        async def on_timeout(self):
            await self.inter.edit_original_message(view=None)
            self.stop()

        @button(label="General Commands", style=disnake.ButtonStyle.blurple)
        async def user(self, _button: disnake.Button, interaction: disnake.Interaction) -> None:
            # General Embed
            general_embed = Embed(color=Colour.blurple())
            general_embed.set_author(name="General Commands")
            general_embed.add_field(name="`/whois`", value="User's Info")
            general_embed.add_field(name="`/botinfo`", value="Bot's Info")
            general_embed.add_field(name="`/stats`", value="Bot's Stats")
            general_embed.add_field(name="`/chat create`", value="Create a new Private Chat", inline=False)
            general_embed.add_field(name="`/introduce`", value="Introduce Yourself", inline=False)
            general_embed.add_field(name="`/help`", value="Get this help message", inline=False)
            general_embed.add_field(name="`/tts`", value="Generate a TTS message", inline=False)
            for child in self.children:
                child.disabled = False
            _button.disabled = True
            await interaction.response.edit_message(embed=general_embed, view=self)

        @button(label="Music Commands", style=disnake.ButtonStyle.blurple)
        async def music(self, _button: disnake.Button, interaction: disnake.Interaction) -> None:
            # Music Commands
            music_embed = Embed(color=Colour.green())
            music_embed.set_author(name="Play Music from YouTube in VC")
            music_embed.add_field(name="`.play`   <search>", value="Search or Enter URL")
            music_embed.add_field(name="`.pause`", value="Pause Music")
            music_embed.add_field(name="`.stop`", value="Disconnect Bot from VC")
            music_embed.add_field(name="`.np`", value="Display Now Playing")
            music_embed.add_field(name="`.queue`", value="Songs in Queue")
            music_embed.add_field(name="`.skip`\t<song_index>", value="Skip Songs")
            music_embed.add_field(name="`.loop`", value="Toggle Loop")
            music_embed.add_field(name="`.jump`\t<song_index>", value="Skip to a Song")
            music_embed.add_field(name="`.filter`", value="Apply Filters to Song")
            for child in self.children:
                child.disabled = False
            _button.disabled = True
            await interaction.response.edit_message(embed=music_embed, view=self)

        @button(label="Fun Commands", style=disnake.ButtonStyle.blurple)
        async def fun(self, _button: disnake.Button, interaction: disnake.Interaction) -> None:
            # Fun Commands
            fun_embed = Embed(color=Colour.dark_orange())
            fun_embed.set_author(name="Fun Stuff")
            fun_embed.add_field(name="`/kill`", value="Delete someone's existence", inline=False)
            fun_embed.add_field(name="`/pp`", value="Measure someone in Inches 🤏", inline=False)
            fun_embed.add_field(name="`/lyrics`", value="Get lyrics from Spotify Activity", inline=False)
            fun_embed.add_field(name="`/ping`", value="Get Bot's Latency", inline=False)
            for child in self.children:
                child.disabled = False
            _button.disabled = True
            await interaction.response.edit_message(embed=fun_embed, view=self)

    @commands.slash_command(description="How may I help you ?")
    async def help(self, inter: disnake.ApplicationCommandInteraction) -> None:
        view = self.HelpButtons()
        view.inter = inter
        await inter.response.send_message("How may I help you ?", view=view)


def setup(client):
    client.add_cog(HelpMe(client))
