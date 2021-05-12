import discord.ext.commands as commands
from discord import Member, Embed

class userinfo(commands.Cog):

	def __init__(self,client):
		self.client = client

	@commands.command()
	@commands.guild_only()
	async def whois(self, ctx, *, user: Member = None):
		if user is None:
			user = ctx.author
		date_format = "%a, %d %b %Y %I:%M %p"
		embed = Embed(color=user.colour, description=user.mention)
		embed.set_author(name=user, icon_url=user.avatar_url)
		embed.set_thumbnail(url=user.avatar_url)
		embed.add_field(name="Joined this server on", value=user.joined_at.strftime(date_format))
		embed.add_field(name="Joined Discord on", value=user.created_at.strftime(date_format))
		embed.add_field(name="Nickname", value=user.nick)
		if len(user.roles) > 1:
			role_string = ' '.join([r.mention for r in user.roles][1:])
			embed.add_field(name=f"Roles [{len(user.roles)-1}]", value=role_string, inline=False)
		perm_string = ', '.join([str(p[0]).replace("_", " ").title() for p in user.guild_permissions if p[1]])
		embed.add_field(name="Guild permissions", value=perm_string, inline=False)
		embed.set_footer(text=f'User ID: {user.id}')
		return await ctx.send(embed=embed)

def setup(client):
	client.add_cog(userinfo(client))