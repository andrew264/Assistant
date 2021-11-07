# Import
from disnake.ext import commands
from disnake import (
    ApplicationCommandInteraction,
    Button,
    ButtonStyle,
    Client,
    Colour,
    Embed,
    Interaction,
)
from disnake.ui import View, button


class HelpMe(commands.Cog):
    def __init__(self, client: Client):
        self.client = client

    class HelpButtons(View):
        def __init__(self):
            super().__init__(timeout=60.0)
            self.value = ""
            self.inter: ApplicationCommandInteraction

        async def on_timeout(self):
            await self.inter.edit_original_message(view=None)
            self.stop()

        @button(label="General Commands", style=ButtonStyle.blurple)
        async def user(self, button: Button, interaction: Interaction) -> None:
            ### general Embed
            generalembed = Embed(color=Colour.blurple())
            generalembed.set_author(name="General Commands")
            generalembed.add_field(name="`/whois`", value="User's Info", inline=True)
            generalembed.add_field(name="`/botinfo`", value="Bot's Info", inline=True)
            generalembed.add_field(
                name="`/chat create`", value="Create a new Private Chat", inline=False
            )
            generalembed.add_field(
                name="`/introduce`", value="Introduce Yourself", inline=False
            )
            generalembed.add_field(
                name="`/help`", value="Get this help message", inline=False
            )
            generalembed.add_field(
                name="`/tts`", value="Generate a TTS message", inline=False
            )
            ###
            await interaction.response.edit_message(embed=generalembed, view=self)

        @button(label="Music Commands", style=ButtonStyle.blurple)
        async def msuic(self, button: Button, interaction: Interaction) -> None:
            ### Music Commands
            musicembed = Embed(color=Colour.green())
            musicembed.set_author(name="Play Music from YouTube in VC")
            musicembed.add_field(name="`.play`   <search>", value="Search or Enter URL")
            musicembed.add_field(name="`.pause`", value="Pause Music")
            musicembed.add_field(name="`.stop`", value="Disconnect Bot from VC")
            musicembed.add_field(name="`.np`", value="Display Now Playing")
            musicembed.add_field(name="`.queue`", value="Songs in Queue")
            musicembed.add_field(name="`.skip`\t<song_index>", value="Skip Songs")
            musicembed.add_field(name="`.loop`", value="Toggle Loop")
            musicembed.add_field(name="`.jump`\t<song_index>", value="Skip to a Song")
            ###
            await interaction.response.edit_message(embed=musicembed, view=self)

        @button(label="Fun Commands", style=ButtonStyle.blurple)
        async def fun(self, button: Button, interaction: Interaction) -> None:
            ### Fun Commands
            funembed = Embed(color=Colour.dark_orange())
            funembed.set_author(name="Fun Stuff")
            funembed.add_field(
                name="`/kill`", value="Delete someone's existance", inline=False
            )
            funembed.add_field(
                name="`/pp`", value="Measure someone in Inches 🤏", inline=False
            )
            funembed.add_field(
                name="`/lyrics`", value="Get lyrics from Spotify Activity", inline=False
            )
            funembed.add_field(name="`/ping`", value="Get Bot's Latency", inline=False)
            ###
            await interaction.response.edit_message(embed=funembed, view=self)

    @commands.slash_command(description="How may I help you ?")
    async def help(self, inter: ApplicationCommandInteraction) -> None:
        view = HelpMe.HelpButtons()
        view.inter = inter
        await inter.response.send_message("How may I help you ?", view=view)


def setup(client):
    client.add_cog(HelpMe(client))
