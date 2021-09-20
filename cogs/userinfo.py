import discord
import discord.ext.commands as commands
from discord import Member, Embed
from discord import Spotify, Game, CustomActivity, Streaming, Activity
from dislash.application_commands import slash_client
from dislash.interactions.application_command import Option, OptionType
from dislash.interactions.app_command_interaction import SlashInteraction
from datetime import datetime, timezone

class userinfo(commands.Cog):

	def __init__(self,client):
		self.client = client

	@commands.command(aliases=['info', 'analyse', 'user', 'userinfo'])
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True)
	async def whois(self, ctx: commands.Context, *, user: Member = None):
		if user is None:
			user = ctx.author
		date_format = "%a, %d %b %Y %I:%M %p"
		embed = Embed(color=user.colour, description=user.mention)
		embed.set_author(name=user, icon_url=user.display_avatar.url)
		embed.set_thumbnail(url=user.display_avatar.url)
		time_now = datetime.now(timezone.utc)
		embed.add_field(name=f"Joined {ctx.guild.name} on", value=f"{user.joined_at.strftime(date_format)}\n**({(time_now - user.joined_at).days} days ago)**")
		embed.add_field(name="Account created on", value=f"{user.created_at.strftime(date_format)}\n**({(time_now - user.created_at).days} days ago)**")
		if user.nick is not None:
			embed.add_field(name="Nickname", value=user.nick)
		# Clients
		if user.raw_status != 'offline':
			embed.add_field(name="Available Clients", value=userinfo.AvailableClients(user))
		# Activity
		for activity in user.activities:
			if isinstance(activity, Game):
				embed.add_field(name="Playing", value=userinfo.ActivityVal(activity))
			elif isinstance(activity, Streaming):
				embed.add_field(name=f"Streaming", value=f"[{activity.name}]({activity.url})")
			elif isinstance(activity, Spotify):
				embed.add_field(name="Spotify", value=f"Listening to [{activity.title} by {', '.join(activity.artists)}]({activity.track_url})")
				embed.set_thumbnail(url=activity.album_cover_url)
			elif isinstance(activity, CustomActivity):
				embed.add_field(name="Status", value=userinfo.CustomActVal(activity))
			elif isinstance(activity, Activity):
				embed.add_field(name=f"{activity.type.name.capitalize()}", value=userinfo.ActivityVal(activity))
				if hasattr(activity, 'large_image_url') and activity.large_image_url is not None:
					embed.set_thumbnail(url=activity.large_image_url)
		if len(user.roles) > 1:
			role_string = ' '.join([r.mention for r in user.roles][1:])
			embed.add_field(name=f"Roles [{len(user.roles)-1}]", value=role_string, inline=False)
		embed.set_footer(text=f'User ID: {user.id}')
		try:
			return await ctx.send(embed=embed)
		except discord.Forbidden:
			return await ctx.send("Missing Embed Permission.")

	def ActivityVal(activity: Activity):
		value: str = f"**{activity.name}** "
		if activity.start is not None:
			delta = (datetime.now(timezone.utc) - activity.start).seconds
			if delta < 60:
				value += f"({delta} s)"
			elif 60 <= delta < 3600:
				value += f"({delta//60} mins {delta%60} sec)"
			elif delta >=3600:
				value += f"({delta//3600} hrs {(delta//60)%60} mins)"
		return value

	def CustomActVal(activity: CustomActivity):
		value: str = ''
		if activity.emoji is not None:
			value += f"[{activity.emoji}]({activity.emoji.url}) "
		if activity.name is not None:
			value += activity.name
		return value

	def AvailableClients(user: Member):
		clients = []
		if user.desktop_status.name != 'offline':
			clients.append('Desktop')
		if user.mobile_status.name != 'offline':
			clients.append('Mobile')
		if user.web_status.name != 'offline':
			clients.append('Web')
		value = f"**{', '.join(clients)}**"
		if user.raw_status == 'online': value = "Online in " + value
		elif user.raw_status == 'idle': value = "Idling in " + value
		elif user.raw_status == 'dnd': value = value + " (DND)"
		return value

	@slash_client.slash_command(
		description="Shows the avatar of the user",
		options=[Option("user", "Mention a user", OptionType.USER)])
	async def avatar(self, ctx: commands.Context, user: Member = None):
		if user is None:
			user = ctx.author
		avatar=Embed(title=f"{user.display_name}'s Avatar 🖼", color=user.colour)
		avatar.set_image(url=user.display_avatar.url)
		await ctx.send(embed=avatar)

	@slash_client.slash_command(description="Shows Bot's Info")
	async def botinfo(self, ctx: commands.Context):
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
