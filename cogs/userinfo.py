# Imports
from disnake.ext import commands
from disnake.ext.commands import Param
from disnake.utils import get
from disnake import Member, Embed, Client
from disnake import Spotify, Game, CustomActivity, Streaming, Activity
from disnake import Option, OptionType, ApplicationCommandInteraction, UserCommandInteraction

from datetime import datetime, timezone
import sqlite3
from platform import python_version

class UserInfo(commands.Cog):

	def __init__(self, client: Client):
		self.client = client

	@commands.slash_command(description="Luk wat he be doin ovar der")
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True)
	async def whois(self, inter: ApplicationCommandInteraction,
				 user: Member = Param(description= "Mention a User", default=lambda inter: inter.author)):
		return await inter.response.send_message(embed=UserInfo.WhoIsEmbed(self, user))

	@commands.user_command(name="Who is this Guy?")
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True)
	async def ContextWhoIs(self, inter: UserCommandInteraction):
		return await inter.response.send_message(embed=UserInfo.WhoIsEmbed(self, inter.target))

	def WhoIsEmbed(self, user: Member):
		# Fetch activity. I really wish i don't have to do this.
		user: Member = get(self.client.get_all_members(), id=user.id)

		date_format = "%a, %d %b %Y %I:%M %p"
		embed = Embed(color=user.colour)
		# Description
		about = UserInfo.GetAboutfromDB(user.id)
		if about is not None: embed.description = f"{user.mention}: {about}"
		else: embed.description=user.mention

		embed.set_author(name=user, icon_url=user.display_avatar.url)
		embed.set_thumbnail(url=user.display_avatar.url)
		time_now = datetime.now(timezone.utc)
		embed.add_field(name=f"Joined {user.guild.name} on", value=f"{user.joined_at.strftime(date_format)}\n**({(time_now - user.joined_at).days} days ago)**")
		embed.add_field(name="Account created on", value=f"{user.created_at.strftime(date_format)}\n**({(time_now - user.created_at).days} days ago)**")
		if user.nick is not None:
			embed.add_field(name="Nickname", value=user.nick)
		# Clients
		if user.raw_status != 'offline':
			embed.add_field(name="Available Clients", value=UserInfo.AvailableClients(user))
		# Activity
		for activity in user.activities:
			if isinstance(activity, Game):
				embed.add_field(name="Playing", value=UserInfo.ActivityVal(activity))
			elif isinstance(activity, Streaming):
				embed.add_field(name=f"Streaming", value=f"[{activity.name}]({activity.url})")
			elif isinstance(activity, Spotify):
				embed.add_field(name="Spotify", value=f"Listening to [{activity.title} by {', '.join(activity.artists)}]({activity.track_url})")
				embed.set_thumbnail(url=activity.album_cover_url)
			elif isinstance(activity, CustomActivity):
				embed.add_field(name="Status", value=UserInfo.CustomActVal(activity))
			elif isinstance(activity, Activity):
				embed.add_field(name=f"{activity.type.name.capitalize()}", value=UserInfo.ActivityVal(activity))
				if hasattr(activity, 'large_image_url') and activity.large_image_url is not None:
					embed.set_thumbnail(url=activity.large_image_url)
		if len(user.roles) > 1:
			role_string = ' '.join([r.mention for r in user.roles][1:])
			embed.add_field(name=f"Roles [{len(user.roles)-1}]", value=role_string, inline=False)
		embed.set_footer(text=f'User ID: {user.id}')
		return embed

	def ActivityVal(activity: Activity):
		value: str = f"**{activity.name}**\n"
		if activity.start is not None:
			value += UserInfo.timeDelta(activity.start)
		return value

	def timeDelta(timestamp: datetime):
		sec = (datetime.now(timezone.utc) - timestamp).seconds
		value:str = ""
		if sec < 60:
			value += f"({sec} s)"
		elif 60 <= sec < 3600:
			value += f"({sec//60} mins {sec%60} sec)"
		elif sec >=3600:
			value += f"({sec//3600} hrs {(sec//60)%60} mins)"
		return value

	def CustomActVal(activity: CustomActivity):
		value: str = ''
		if activity.emoji is not None:
			value += f"[{activity.emoji}]({activity.emoji.url}) "
		if activity.name is not None:
			value += f"**{activity.name}**"
		value += f"\n{UserInfo.timeDelta(activity.created_at)}"
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

	@commands.slash_command(description="Shows the avatar of the user")
	async def avatar(self, inter: ApplicationCommandInteraction,
				  user: Member = Param(description= "Mention a User", default=lambda inter: inter.author)):
		avatar=Embed(title=f"{user.display_name}'s Avatar 🖼", color=user.colour)
		avatar.set_image(url=user.display_avatar.url)
		await inter.response.send_message(embed=avatar)

	@commands.user_command(name='Avatar')
	async def ContextAvatar(self, inter: UserCommandInteraction):
		avatar=Embed(title=f"{inter.target.display_name}'s Avatar 🖼")
		avatar.set_image(url=inter.target.display_avatar.url)
		await inter.response.send_message(embed=avatar)

	@commands.slash_command(description="Shows Bot's Info")
	async def botinfo(self, inter: ApplicationCommandInteraction):
		user = self.client.user
		embed = Embed(color=0xFF0060, description=user.mention)
		embed.set_author(name=user, icon_url=user.avatar.url)
		embed.set_thumbnail(url=user.avatar.url)
		embed.add_field(name="Created by", value='Andrew', inline=False)
		embed.add_field(name="Created on", value='21 Mar 2021', inline=False)
		embed.add_field(name="Python Version", value=f'v{python_version()}', inline=False)
		embed.set_footer(text=f'User ID: {user.id}')
		return await inter.response.send_message(embed=embed)
	
	@commands.slash_command(description = "Introduce Yourself to Others.",
							options=[Option("message", "Enter a message", OptionType.string, required = True)])
	async def introduce(self, inter: ApplicationCommandInteraction, message: str):
		UserInfo.AddDatatoDB(userID=inter.author.id, message=message.replace('"', ''))
		await inter.response.send_message("Introduction Added.")

	def AddDatatoDB(userID: int, message: str):
		conn = sqlite3.connect('./data/database.sqlite3')
		#conn.execute("CREATE TABLE Members (USERID INT PRIMARY KEY NOT NULL, ABOUT TEXT);")
		alreadyExists = conn.execute(f"SELECT EXISTS(SELECT 1 FROM Members WHERE USERID = {userID})").fetchone()[0]
		if alreadyExists: conn.execute(f"""UPDATE Members SET ABOUT = "{message}" WHERE USERID = {userID}""")
		else: conn.execute(f"""INSERT INTO Members (USERID, ABOUT) VALUES ({userID}, "{message}")""")
		conn.commit()
		conn.close()
	
	def GetAboutfromDB(userID: int):
		conn = sqlite3.connect('./data/database.sqlite3')
		alreadyExists = conn.execute(f"SELECT EXISTS(SELECT 1 FROM Members WHERE USERID = {userID})").fetchone()[0]
		if alreadyExists:
			about = [row[1] for row in conn.execute(f"SELECT * FROM Members WHERE USERID = {userID}")]
			conn.close()
			return about[0]
		else: return None

def setup(client):
	client.add_cog(UserInfo(client))