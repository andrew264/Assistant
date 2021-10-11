# Imports
from disnake.ext import commands
from disnake import Embed, RawReactionActionEvent, Client
from disnake import Member, PartialMessage, TextChannel
from disnake.utils import get

CHANNEL_ID = 826931734645440562
MESSAGE_ID = 891793035959078932

possibleEmojis = {
	'🟥' : "Colour-Red",
	'🟦' : "Colour-Blue",
	'🟩' : "Colour-Green",
	'🟫' : "Colour-Brown",
	'🟧' : "Colour-Orange",
	'🟪' : "Colour-Purple",
	'🟨' : "Colour-Yellow"
	}


class ReactionRoles(commands.Cog):

	def __init__(self, client: Client):
		self.client = client

	@commands.Cog.listener()
	async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
		if payload.channel_id != CHANNEL_ID: return
		if payload.message_id != MESSAGE_ID: return
		if payload.member.bot == True: return

		channel: TextChannel = self.client.get_channel(payload.channel_id)
		message: PartialMessage = channel.get_partial_message(payload.message_id)

		# filter out other emojis
		if payload.emoji.name not in possibleEmojis.keys():
			return await message.remove_reaction(payload.emoji, payload.member)

		# remove duplicate emojis
		for emoji in possibleEmojis.keys():
			if emoji != payload.emoji.name:
				await message.remove_reaction(emoji, payload.member)

		# remove any colour roles
		for role in payload.member.roles:
			if role.name.startswith("Colour-"):
				await payload.member.remove_roles(role)

		# assign the particular role
		role = get(payload.member.guild.roles, name=possibleEmojis[payload.emoji.name])
		await payload.member.add_roles(role)

	@commands.Cog.listener()
	async def on_raw_reaction_remove(self, payload: RawReactionActionEvent):
		if payload.channel_id != CHANNEL_ID: return
		if payload.message_id != MESSAGE_ID: return
		# filter out other emojis
		if payload.emoji.name not in possibleEmojis.keys(): return

		# filter bots out
		member: Member = get(self.client.get_all_members(), id=payload.user_id)
		if member.bot == True: return

		# just remove all colour roles for member
		for role in member.roles:
			if role.name.startswith("Colour-"):
				await member.remove_roles(role)

	@commands.command()
	@commands.is_owner()
	async def reactionroles(self, ctx: commands.Context):
		await ctx.message.delete()
		embed = Embed(title = "Reaction Roles", colour = 0xffffff, description = "Claim a colour of your choice!")
		msg = await ctx.send(embed=embed)
		for emoji in possibleEmojis.keys():
			await msg.add_reaction(emoji)

def setup(client):
	client.add_cog(ReactionRoles(client))