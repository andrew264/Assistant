import discord.ext.commands as commands
from discord import Embed, Colour
from discord import Message, Member, User, VoiceState, TextChannel
from discord import CustomActivity
from datetime import datetime
from olenv import OWNERID

# IDs
CHANNEL_ID = 891369472101863494

class Surveillance(commands.Cog):

	def __init__(self,client):
		self.client = client

	@commands.Cog.listener()
	async def on_message_edit(self, before: Message, after: Message):
		if before.author.bot: return
		if before.author.id == OWNERID: return
		if before.clean_content == after.clean_content: return
		log_channel: TextChannel = self.client.get_channel(CHANNEL_ID)
		embed = Embed(colour = Colour.teal())
		embed.set_author(name=f"{before.author} edited a message in #{before.channel.name}", icon_url=before.author.avatar.url)
		embed.add_field(name="Original Message",value=before.clean_content, inline=False)
		embed.add_field(name="Altered Message",value=after.clean_content, inline=False)
		embed.set_footer(text=f"{datetime.now().strftime('%I:%M %p, %d %b')}")
		await log_channel.send(embed=embed)

	@commands.Cog.listener()
	async def on_message_delete(self, message: Message):
		if message.author.bot: return
		log_channel: TextChannel = self.client.get_channel(CHANNEL_ID)
		embed = Embed(colour = Colour.orange())
		embed.set_author(name=f"{message.author} deleted a message in #{message.channel.name}", icon_url=message.author.avatar.url)
		embed.add_field(name="Message Content", value=message.content, inline=False)
		embed.set_footer(text=f"{datetime.now().strftime('%I:%M %p, %d %b')}")
		await log_channel.send(embed=embed)

	@commands.Cog.listener()
	async def on_member_update(self, before: Member, after: Member):
		if before.bot: return
		if before.id == OWNERID: return
		if before.display_name == after.display_name: return
		log_channel: TextChannel = self.client.get_channel(CHANNEL_ID)
		embed = Embed(colour = Colour.dark_orange())
		embed.set_author(name=f"{before} updated their Nickname", icon_url=before.avatar.url)
		embed.add_field(name="Old Name",value=before.display_name, inline=False)
		embed.add_field(name="New Name",value=after.display_name, inline=False)
		embed.set_footer(text=f"{datetime.now().strftime('%I:%M %p, %d %b')}")
		await log_channel.send(embed=embed)

	@commands.Cog.listener()
	async def on_user_update(self, before: User, after: User):
		if before.bot: return
		if before.id == OWNERID: return
		if before.name == after.name & before.discriminator == after.discriminator: return
		log_channel: TextChannel = self.client.get_channel(CHANNEL_ID)
		embed = Embed(colour = Colour.brand_green())
		embed.set_author(name=f"{before} updated their Username", icon_url=before.avatar.url)
		embed.add_field(name="Old Username",value=f"{before.name} #{before.discriminator}", inline=False)
		embed.add_field(name="New Username",value=f"{after.name} #{after.discriminator}", inline=False)
		embed.set_footer(text=f"{datetime.now().strftime('%I:%M %p, %d %b')}")
		await log_channel.send(embed=embed)

	@commands.Cog.listener()
	async def on_presence_update(self, before: Member, after: Member):
		if before.bot: return
		if before.id == OWNERID: return
		log_channel: TextChannel = self.client.get_channel(CHANNEL_ID)
		embed = Embed(colour = Colour.gold())
		embed.set_author(name=f"{before.name}'s Presence update", icon_url=before.avatar.url)
		if Surveillance.StatusUpdate(before) != Surveillance.StatusUpdate(after):
			embed.add_field(name=f"Status Update", value=f"{Surveillance.StatusUpdate(before)} ──> {Surveillance.StatusUpdate(after)}")
		if Surveillance.AvailableClients(before) != Surveillance.AvailableClients(after) :
			embed.add_field(name=f"Client Update", value=f"{Surveillance.AvailableClients(before)} ──> {Surveillance.AvailableClients(after)}", inline=False)
		if before.activity != after.activity:
			if isinstance(after.activity, CustomActivity) and isinstance(before.activity, CustomActivity):
				if Surveillance.CustomActVal(before.activity) != Surveillance.CustomActVal(after.activity):
					embed.add_field(name=f"Custom Activity", value=f"{Surveillance.CustomActVal(before.activity)}\n──>\n{Surveillance.CustomActVal(after.activity)}", inline=False)
			elif before.activity is None and after.activity is not None:
				embed.add_field(name=f"Activity Update", value=f"Started: {after.activity.type.name.capitalize()} {after.activity.name}", inline=False)
			elif before.activity is not None and after.activity is None:
				embed.add_field(name=f"Activity Update", value=f"Stoped: {before.activity.type.name.capitalize()} {before.activity.name}", inline=False)
			elif before.activity is not None and after.activity is not None and before.activity.name != after.activity.name:
				embed.add_field(name=f"Activity Update", value=f"{before.activity.type.name.capitalize()}: {before.activity.name}\n──>\n{after.activity.type.name.capitalize()}: {after.activity.name}", inline=False)
		if len(embed.fields):
			await log_channel.send(embed=embed)

	@commands.Cog.listener()
	async def on_voice_state_update(self, member: Member, before: VoiceState, after: VoiceState):
		if member.bot: return
		if after.channel == before.channel: return
		log_channel: TextChannel = self.client.get_channel(CHANNEL_ID)
		if after.channel is None:
			await log_channel.send(f"{member.display_name} left {before.channel.mention}",delete_after = 900)
		if before.channel is None:
			await log_channel.send(f"{member.display_name} joined {after.channel.mention}",delete_after = 900)
		elif after.channel is not None and before.channel is not None:
			await log_channel.send(f"{member.display_name} moved to {after.channel.mention} from {before.channel.mention}",delete_after = 900)

	@commands.Cog.listener()
	async def on_typing(self, channel: TextChannel, user: Member, when: datetime):
		if user.bot: return
		if user.id == OWNERID: return
		if channel.name != "general-shit" and channel.name != "private-chat": return
		log_channel: TextChannel = self.client.get_channel(CHANNEL_ID)
		await log_channel.send(f"{user.display_name} started typing in {channel.mention}", delete_after = 120)

	def AvailableClients(user: Member):
		clients = []
		if user.desktop_status.name != 'offline':
			clients.append('Desktop')
		if user.mobile_status.name != 'offline':
			clients.append('Mobile')
		if user.web_status.name != 'offline':
			clients.append('Web')
		if clients == []: return "Offline"
		return f"{', '.join(clients)}"

	def StatusUpdate(user: Member):
		if user.raw_status == 'online': return "Online"
		elif user.raw_status == 'idle': return "Idle"
		elif user.raw_status == 'dnd': return "Do not Disturb"
		elif user.raw_status == 'offline': return "Offline"

	def CustomActVal(activity: CustomActivity):
		value: str = ''
		if activity.emoji is not None:
			value += f"[{activity.emoji}]({activity.emoji.url}) "
		if activity.name is not None:
			value += activity.name
		return value

def setup(client):
	client.add_cog(Surveillance(client))