from discord.ext import commands, tasks
import asyncio
from discord import Member
from olenv import OWNERID

sec = 10
class muteop(commands.Cog):

	def __init__(self,client):
		self.client = client

	@commands.command()
	@commands.has_permissions(manage_messages=True)
	async def muteop(self, ctx, member: Member = None, duration:int=10):
		if ctx.author.guild_permissions.administrator or ctx.author.id == OWNERID :
			global sec
			if member is None:
				member = ctx.author
			if duration:
				sec = duration
			if sec > 300 or sec < 0:
				await ctx.reply(f"{member.name} pavam guys")
			if 1 < sec < 301:
				await ctx.reply(f'Muted {member.name} for {sec} sec')
				while sec>0 and sec <= 300:
					await member.edit(mute=True)
					await asyncio.sleep(1)
					sec = sec-1
					print(sec)
					if sec == 0:
						await members.edit(mute=False)
		else: await ctx.send("😰No")

	@commands.command(aliases=['unmute'])
	@commands.has_permissions(manage_messages=True)
	async def unmuteop(self, ctx):
		global sec
		sec=1
		await asyncio.sleep(1)
		sec=10


def setup(client):
	client.add_cog(muteop(client))