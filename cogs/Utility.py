# Imports
from disnake.ext import commands
from disnake.ext.commands import Param
from disnake import (
	Activity,
	ActivityType,
	ApplicationCommandInteraction,
	Client,
	Status,
	Member,
	Message,
	MessageCommandInteraction,
	User,
	)

from typing import Optional

class Utility(commands.Cog):

	def __init__(self, client: Client):
		self.client = client

	# echo
	@commands.command(hidden=True)
	@commands.is_owner()
	async def echo(self,
				ctx: commands.Context,
				*, args) -> None:
		await ctx.send(args)
		await ctx.message.delete()

	# ping
	@commands.slash_command(description = "Get Bot's Latency")
	async def ping(self, inter: ApplicationCommandInteraction) -> None:
		await inter.response.send_message(f'Client Latency: {round(self.client.latency * 1000)}  ms')

	#Set Status
	State = commands.option_enum({"Online": 'online', "Idle": 'idle', "Do not Disturb": 'dnd',"Invisible": 'offline'})
	ActType = commands.option_enum({"Playing": '0', "Streaming": '1', "Listening": '2', "Watching": '3'})
	@commands.slash_command(description = "Set Bot's Activity")
	@commands.is_owner()
	async def status(self,
				  inter: ApplicationCommandInteraction,
				  state: State = Param(description="Set Bot's Status"),
				  type: ActType = Param(description="Set Bot's Activity Type"),
				  name: str = Param(description="Set Bot's Activity Name", default="yall Homies")) -> None:
		await self.client.change_presence(status=Status(state), activity=Activity(type=ActivityType(int(type)), name=name))
		await inter.response.send_message(f'Status set to `{Status(state).name.capitalize()}` and `{ActivityType(int(type)).name.title()}: {name}`', ephemeral=True)

	# clear
	@commands.command(aliases=['delete'])
	@commands.has_permissions(administrator=True)
	async def clear(self,
				 ctx: commands.Context,
				 user: Optional[User],
				 no_of_msgs: Optional[int] = 5) -> None:
		if no_of_msgs > 420:
			return await ctx.reply(f'No')
		await ctx.message.delete()
		if user is not None:
			def check(msg: Message):
				return msg.author.id == user.id
			await ctx.channel.purge(limit=no_of_msgs, check=check)
			return await ctx.send(f'`{ctx.author.display_name}` deleted `{user.display_name}\'s` `{no_of_msgs}` message(s).', delete_after=30)
		else:
			await ctx.channel.purge(limit=no_of_msgs)
			return await ctx.send(f'`{ctx.author.display_name}` deleted `{no_of_msgs}` message(s).', delete_after=30)
	
	# Context Delete
	@commands.message_command(name="Delete till HERE")
	@commands.has_permissions(administrator=True)
	async def ContextClear(self, inter: MessageCommandInteraction) -> None:
		await inter.channel.purge(after=inter.target)
		await inter.response.send_message(f"`{inter.author.display_name}` deleted messages till `{inter.target.author.display_name}\'s` message", ephemeral=True)

	@commands.command(aliases=['yeet'])
	@commands.is_owner()
	async def purge_user(self, ctx: commands.Context, user: Member= None) -> None:
		if user is None:
			return await ctx.send("Mention Someone")
		await ctx.send(f'Fetching messages from {ctx.channel.mention}', delete_after=30)
		messages = await ctx.channel.history(limit=69420).flatten()
		await ctx.send(f'Fetched {len(messages)} messages', delete_after=30)
		counter = 0
		for message in messages:
			if message.author.id == user.id or str(user.id) in message.content:
				await message.delete()
				counter +=1
		if counter >0:
			await ctx.send(f'Deleted {counter} messages.', delete_after=30)

def setup(client):
	client.add_cog(Utility(client))