import discord
import discord.ext.commands as commands
from discord import Member, Embed
from discord import Spotify, CustomActivity, Game, Streaming, Activity
from dislash.application_commands import slash_client
from dislash.interactions.application_command import Option, OptionType
from datetime import datetime, timezone

class userinfo(commands.Cog):

	def __init__(self,client):
		self.client = client

	@commands.command(aliases=['info', 'analyse', 'user', 'userinfo'])
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True)
	async def whois(self, ctx, *, user: Member = None):
		if user is None:
			user = ctx.author
		date_format = "%a, %d %b %Y %I:%M %p"
		embed = Embed(color=user.colour, description=user.mention)
		if user.avatar.url:
			embed.set_author(name=user, icon_url=user.avatar.url)
			embed.set_thumbnail(url=user.avatar.url)
		else: embed.set_author(name=user)
		time_now = datetime.now(timezone.utc)
		embed.add_field(name=f"Joined {ctx.guild.name} on", value=f"{user.joined_at.strftime(date_format)}\n**({(time_now - user.joined_at).days} days ago)**")
		embed.add_field(name="Joined Discord on", value=f"{user.created_at.strftime(date_format)}\n**({(time_now - user.created_at).days} days ago)**")
		embed.add_field(name="Nickname", value=user.nick)
		# Clients
		if user.raw_status != 'offline':
			embed.add_field(name="Available Clients", value=f"**{userinfo.clients(self, user)}**")
		# Activity
		for activity in user.activities:
			if activity.type.name == 'playing':
				if activity.start is not None: embed.add_field(name="Playing", value=f"**{activity.name}** ({':'.join(str(time_now - activity.start).split(':')[:2])} hours)")
				else: embed.add_field(name="Playing", value=f"**{activity.name}**")
			elif activity.type.name == 'streaming':
				embed.add_field(name=f"Streaming", value=f"[{activity.name}]({activity.url})")
			elif activity.type.name == 'listening':
				embed.add_field(name="Spotify", value = f"Listening to [{activity.title} by {', '.join(activity.artists)}]({activity.track_url})")
			elif activity.type.name == 'custom':
				embed.add_field(name="Status", value=f'{activity.emoji} {activity.name}')
		if len(user.roles) > 1:
			role_string = ' '.join([r.mention for r in user.roles][1:])
			embed.add_field(name=f"Roles [{len(user.roles)-1}]", value=role_string, inline=False)
		embed.set_footer(text=f'User ID: {user.id}')
		try:
			return await ctx.send(embed=embed)
		except discord.Forbidden:
			return await ctx.send("Missing Embed Permission.")

	def clients(self, user: Member):
		clients = []
		if user.desktop_status.name != 'offline':
			clients.append('Desktop')
		if user.mobile_status.name != 'offline':
			clients.append('Mobile')
		if user.web_status.name != 'offline':
			clients.append('Web')
		return ', '.join(clients)

	@slash_client.slash_command(
		description="Shows the avatar of the user",
		options=[Option("user", "Mention a user", OptionType.USER)])
	async def avatar(self, ctx, *, user: Member = None):
		if user is None:
			user = ctx.author
		avatar=Embed(title=f"{user.display_name}'s profile pic :)", color=user.colour)
		avatar.set_image(url=user.avatar.url)
		await ctx.send(embed=avatar)

	@slash_client.slash_command(description="Shows Bot's Info")
	async def botinfo(self, ctx):
		user = self.client.user
		embed = Embed(color=0xFF0060, description=user.mention)
		embed.set_author(name=user, icon_url=user.avatar.url)
		embed.set_thumbnail(url=user.avatar.url)
		embed.add_field(name="Created by", value='Andrew', inline=False)
		embed.add_field(name="Created on", value='21 Mar 2021', inline=False)
		embed.add_field(name="Created for", value='Personal Purposes', inline=False)
		embed.set_footer(text=f'User ID: {user.id}')
		return await ctx.send(embed=embed)

def setup(client):
	client.add_cog(userinfo(client))