# discord stuff
import discord.ext.commands as commands
from discord import Embed
from discord.member import Member
from discord.utils import find
from dislash.application_commands import slash_client
from dislash.interactions.application_command import Option, OptionType
from dislash.interactions.app_command_interaction import SlashInteraction

# random stuff
from random import randint, choice

class fun(commands.Cog):

	def __init__(self,client):
		self.client = client

	@slash_client.slash_command(
		description="Measure them PPs",
		options=[Option("user", "Mention a user", OptionType.USER)])
	async def pp(self, inter: SlashInteraction, user: Member = None):
		if user is None:
			user = inter.author
		pp404 = find(lambda r: r.id == 838868317779394560, inter.guild.roles)
		ppembed = Embed(colour = user.color)
		ppembed.set_author(name=user, icon_url=user.avatar.url)
		if pp404 in user.roles: ppembed.add_field(name="There is no sign of PP in here.", value='\u200b')
		elif user.bot: ppembed.add_field(name="There is no sign of life in here.", value='\u200b')
		else: ppembed.add_field(name=f"{user.display_name}'s PP:", value=f"8{'='*randint(0,9)}D")
		ppembed.set_footer(text=f'Inspected by: {inter.author.display_name}')
		return await inter.send(embed=ppembed)

	@slash_client.slash_command(
		description="Delete their existance",
		options=[Option("user", "Mention a user", OptionType.USER)])
	async def kill(self, inter: SlashInteraction, user: Member = None):
		if user is None or user == inter.author :
			return await inter.send('Stop, Get some Help.')
		killembed = Embed(colour = user.color)
		killembed.set_author(name=user, icon_url=user.avatar.url)
		if user.bot: killembed.add_field(name='You cannot attack my kind.', value='\u200b')
		else: killembed.add_field(name=fun.deathmsggen(user.display_name, inter.author.display_name), value='\u200b')
		return await inter.send(embed=killembed)

	def deathmsggen(victim, killer):
		deathmsgs = [' was shot by ', ' drowned whilst trying to escape ', ' was blown up by ', ' was killed by ', ' walked into fire whilst fighting ', ' was struck by lightning whilst fighting ',
			   ' was frozen to death by ', ' was slain by ', ' was squashed by ', ' was killed trying to hurt ', ' didn\'t want to live in the same world as ', ' died because of ', ' was doomed to fall by ',
			   ' got finished off by ', ' was drowned by ']
		if randint(0,6): return victim+choice(deathmsgs)+killer
		else : return killer+choice(deathmsgs)+victim

def setup(client):
	client.add_cog(fun(client))