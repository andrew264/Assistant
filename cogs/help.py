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

	@slash_client.slash_command(description="How may I help you")
	async def help(self, inter):
		row = ActionRow(
            Button(style=ButtonStyle.blurple, label="User Info", custom_id="user"),
            Button(style=ButtonStyle.blurple, label="Cleaning Commands", custom_id="clean"),
            Button(style=ButtonStyle.blurple, label="Music Commands", custom_id="music"),
            Button(style=ButtonStyle.blurple, label="Minecraft Commands", custom_id="mc")
        )
		msg = await inter.reply('Slash Commands are not listed here.', components=[row])
		on_click = msg.create_click_listener(timeout=120)

		### User Embed 
		userembed = Embed(color = Colour.blurple())
		userembed.set_author(name='User Info',icon_url=self.client.user.avatar.url)
		userembed.add_field(name='`+whois`\t<@User>\t\t\tUser\'s Info', value='\u200b', inline=False)
		userembed.add_field(name='`+aboutme`\t\t\t\t\t\t\t  Bot\'s Info', value='\u200b', inline=False)
		###

		### Chat Cleaning
		cleanembed = Embed(color = Colour.blurple())
		cleanembed.set_author(name='Cleanse The Chat',icon_url=self.client.user.avatar.url)
		cleanembed.add_field(name='`+clear`\t<@User>\t<No_of_Msgs>\t\t  Delete No. of Msgs', value='\u200b', inline=False)
		cleanembed.add_field(name='`+yeetill`\t<MessageID>\t\t\t\t\t\t\t   Delete till that Msg', value='\u200b', inline=False)
		cleanembed.add_field(name='`+yeetmsg`\t<string>\t<No_of_Msgs>\t\tDelete No. of Msgs Containing that String', value='\u200b', inline=False)
		###

		### Music Commands
		musicembed = Embed(color = Colour.green())
		musicembed.set_author(name='Play Music from YouTube in VC',icon_url=self.client.user.avatar.url)
		musicembed.add_field(name='`.play`   <search>', value='Search or Enter URL')
		musicembed.add_field(name='`.pause`', value='Pause Music')
		musicembed.add_field(name='`.stop`', value='Disconnect Bot from VC')
		musicembed.add_field(name='`.np`', value='Display Now Playing')
		musicembed.add_field(name='`.queue`', value='Songs in Queue')
		musicembed.add_field(name='`+skip`\t<song_index>', value='Skip Songs')
		musicembed.add_field(name='`+loop`', value='Toggle Loop')
		musicembed.add_field(name='`+jump`\t<song_index>', value='Skip to a Song')
		###

		### Minecraft Commands
		mcembed = Embed(color = Colour.red())
		mcembed.set_author(name='Admin Commands',icon_url=self.client.user.avatar.url)
		mcembed.add_field(name='`.mcstatus`\t\t\t\t\t\t\t\t\t\t  Check Minecraft Server Status', value='\u200b', inline=False)
		mcembed.add_field(name='`.mcnew`\t<seed[Optional]>\t\tCreate Minecraft Server', value='\u200b', inline=False)
		###

		@on_click.matching_id("user")
		async def on_user(inter):
			await inter.reply(embed = userembed, ephemeral=True)
		@on_click.matching_id("clean")
		async def on_clean(inter):
			await inter.reply(embed = cleanembed, ephemeral=True)
		@on_click.matching_id("music")
		async def on_music(inter):
			await inter.reply(embed = musicembed, ephemeral=True)
		@on_click.matching_id("mc")
		async def on_mc(inter):
			await inter.reply(embed = mcembed, ephemeral=True)
		@on_click.timeout
		async def on_timeout():
			await msg.edit(components=[])

def setup(client):
	client.add_cog(HelpMe(client))