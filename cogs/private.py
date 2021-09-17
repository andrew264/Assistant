# discord stuff
import discord
import discord.ext.commands as commands
from dislash.application_commands import slash_client
from dislash.interactions.app_command_interaction import SlashInteraction

class private(commands.Cog):

	def __init__(self,client):
		self.client = client

	#Create private category for DMs
	@slash_client.slash_command(description="Create a Private Chat & VC.")
	async def chat(self, inter: SlashInteraction):
		pass

	@chat.sub_command(description="Create a new Private Chat.")
	async def create(self, inter: SlashInteraction):
		overwrites_readEnable = discord.PermissionOverwrite()
		overwrites_readEnable.read_messages = True
		for category in inter.guild.categories:
			if category.name == f"{inter.author.display_name}'s Chat" and isinstance(inter.author, discord.Member):
				for channel in category.channels:
					await channel.set_permissions(inter.author, overwrite=overwrites_readEnable)
				await category.set_permissions(inter.author, overwrite=overwrites_readEnable)
				return await inter.reply(f"Created a new Private Chat ({category.mention}).", ephemeral=True)
		overwrites_readTrue = {
			inter.guild.default_role: discord.PermissionOverwrite(read_messages=False),
			inter.guild.me: discord.PermissionOverwrite(read_messages=True),
			inter.author: discord.PermissionOverwrite(read_messages=True)
		}
		category: discord.CategoryChannel = await inter.guild.create_category(f"{inter.author.display_name}'s Chat", overwrites=overwrites_readTrue, reason=None, position=None)
		await category.create_text_channel("Chat", overwrites=overwrites_readTrue)
		await category.create_voice_channel("Private Voice", overwrites=overwrites_readTrue)
		await inter.reply(f"Created a new Private Chat ({category.mention}).", ephemeral=True)

	@chat.sub_command(description="Delete existing Private Chat.")
	async def delete(self, inter: SlashInteraction):
		overwrites_readFalse = discord.PermissionOverwrite()
		overwrites_readFalse.read_messages = False
		category = None
		for i in inter.guild.categories:
			if i.name == f"{inter.author.display_name}'s Chat":
				category = i
			else: category = None
		if isinstance(category, discord.CategoryChannel) and isinstance(inter.author, discord.Member):
			for channel in category.channels:
				await channel.set_permissions(inter.author, overwrite=overwrites_readFalse)
			await category.set_permissions(inter.author, overwrite=overwrites_readFalse)
			return await inter.reply("Private Chat Deleted.", ephemeral=True)
		elif category is None:
			return await inter.reply("You don't have a Private Chat", ephemeral=True)

def setup(client):
	client.add_cog(private(client))