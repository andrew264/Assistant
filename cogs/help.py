# discord stuff
from discord.ext import commands
from discord import Embed, Colour
from dislash.application_commands import slash_client
from dislash.interactions.application_command import Option, OptionType
from dislash.interactions.message_components import ActionRow, Button, ButtonStyle

# .env variables
from olenv import OWNERID

class HelpMe(commands.Cog):

	def __init__(self,client):
		self.client = client

	@slash_client.slash_command(description="How may I help you ?")
	async def help(self, inter):
		row = ActionRow(
            Button(style=ButtonStyle.blurple, label="General Commands", custom_id="general"),
            Button(style=ButtonStyle.blurple, label="Music Commands", custom_id="music"),
            Button(style=ButtonStyle.blurple, label="Fun Commands", custom_id="fun")
        )
		msg = await inter.reply('How may I help you ?', components=[row])
		on_click = msg.create_click_listener(timeout=120)

		### general Embed 
		generalembed = Embed(color = Colour.blurple())
		generalembed.set_author(name='General Commands',icon_url=self.client.user.avatar.url)
		generalembed.add_field(name='`/whois`', value='User\'s Info', inline=True)
		generalembed.add_field(name='`/botinfo`', value='Bot\'s Info', inline=True)
		generalembed.add_field(name='`/chat create`', value='Create a new Private Chat', inline=False)
		generalembed.add_field(name='`/introduce`', value='Introduce Yourself', inline=False)
		generalembed.add_field(name='`/help`', value='Get this help message', inline=False)
		generalembed.add_field(name='`/tts`', value='Generate a TTS message', inline=False)
		###

		### Music Commands
		musicembed = Embed(color = Colour.green())
		musicembed.set_author(name='Play Music from YouTube in VC',icon_url=self.client.user.avatar.url)
		musicembed.add_field(name='`.play`   <search>', value='Search or Enter URL')
		musicembed.add_field(name='`.pause`', value='Pause Music')
		musicembed.add_field(name='`.stop`', value='Disconnect Bot from VC')
		musicembed.add_field(name='`.np`', value='Display Now Playing')
		musicembed.add_field(name='`.queue`', value='Songs in Queue')
		musicembed.add_field(name='`.skip`\t<song_index>', value='Skip Songs')
		musicembed.add_field(name='`.loop`', value='Toggle Loop')
		musicembed.add_field(name='`.jump`\t<song_index>', value='Skip to a Song')
		###

		### Fun Commands
		funembed = Embed(color = Colour.dark_orange())
		funembed.set_author(name='Fun Stuff',icon_url=self.client.user.avatar.url)
		funembed.add_field(name='`/kill`', value='Delete someone\'s existance', inline=False)
		funembed.add_field(name='`/pp`', value='Measure someone in Inches 🤏', inline=False)
		funembed.add_field(name='`/lyrics`', value='Get lyrics from Spotify Activity', inline=False)
		funembed.add_field(name='`/ping`', value='Get Bot\'s Latency', inline=False)
		###

		@on_click.matching_id("general")
		async def on_user(inter):
			await inter.reply(embed = generalembed, ephemeral=True)
		@on_click.matching_id("music")
		async def on_music(inter):
			await inter.reply(embed = musicembed, ephemeral=True)
		@on_click.matching_id("fun")
		async def on_music(inter):
			await inter.reply(embed = funembed, ephemeral=True)
		@on_click.timeout
		async def on_timeout():
			await msg.edit(components=[])

def setup(client):
	client.add_cog(HelpMe(client))