# discord stuff
import discord
import discord.ext.commands as commands
from dislash.application_commands import slash_client
from dislash.interactions.application_command import Option, OptionType
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
		for i in inter.guild.categories:
				if i.name == f"{inter.author.display_name}'s Chat":
					return await inter.reply("Don't you already have one ?", ephemeral=True)
		overwrites = {
			inter.guild.default_role: discord.PermissionOverwrite(read_messages=False),
			inter.guild.me: discord.PermissionOverwrite(read_messages=True),
			inter.author: discord.PermissionOverwrite(read_messages=True)
		}
		category: discord.CategoryChannel = await inter.guild.create_category(f"{inter.author.display_name}'s Chat", overwrites=overwrites, reason=None, position=None)
		await category.create_text_channel("Chat", overwrites=overwrites)
		await category.create_voice_channel("Private Voice", overwrites=overwrites)
		await inter.reply(f"Created a new Private Chat ({category.mention}).", ephemeral=True)

	@chat.sub_command(description="Delete existing Private Chat.")
	async def delete(self, inter: SlashInteraction):
		for i in inter.guild.categories:
			if i.name == f"{inter.author.display_name}'s Chat":
				category: discord.CategoryChannel = i
			else: category = None
		if category is not None:
			for channel in category.channels:
				await channel.delete()
			await category.delete()
			return await inter.reply("Private Chat Deleted.", ephemeral=True)
		elif category is None:
			return await inter.reply("You don't have a Private Chat", ephemeral=True)

def setup(client):
	client.add_cog(private(client))