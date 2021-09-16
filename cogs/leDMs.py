# discord stuff
import discord.ext.commands as commands
from discord import User

# .env variables
from olenv import DM_Channel

class leDMs(commands.Cog):

	def __init__(self,client):
		self.client = client

	# Replies
	@commands.Cog.listener()
	async def on_message(self, message):
		if message.guild: return
		if message.author.bot: return
		if message.author == self.client.user: return
		else:
			channel = self.client.get_channel(DM_Channel)
			await channel.send(f'UserID: `{message.author.id}`\nMessage Author: `{message.author}`\nMessage:\n {message.content} \n──────────────────────────────')

	# slide to dms
	@commands.command()
	@commands.has_permissions(administrator=True)
	async def dm(self, ctx,  user: User, *, msg:str):
		channel = await user.create_dm()
		try:
			await channel.send(msg)
		except Exception: 
			await ctx.send(f'Failed to DM {user}.')

def setup(client):
	client.add_cog(leDMs(client))