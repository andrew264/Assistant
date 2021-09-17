import discord.ext.commands as commands
from discord import Embed
from aiohttp import ClientSession
from os import system
from mcstatus import MinecraftServer
from typing import Optional
from asyncio import sleep
from shutil import copyfile

class mc(commands.Cog):

	def __init__(self,client):
		self.client = client
	
	async def serverstat(self):	
		server = MinecraftServer.lookup("192.168.1.36:42069")
		try :
			status = server.status()
			self.online = True
			self.ppl_online = f'{status.players.online}/{status.players.max}'
			# Fetch IP
			async with ClientSession() as session:
				async with session.get('https://ident.me') as response:
						self.ip = await response.text()+':42069'
		except WindowsError as e:
			if e.winerror == 10061:
				self.online=False

	# startup server
	@commands.command(pass_context=True, aliases=['minecraft', 'startserver', 'start'])
	@commands.has_permissions(manage_messages=True)
	async def mcstart(self, ctx: commands.Context):
		async with ctx.typing():
			await mc.serverstat(self)
			if self.online:
				return await ctx.send('Server is already up and running...')
			else:
				system("start cmd /K 17.bat")
				return await ctx.send('Server will start in 20 secs...')

	# server status
	@commands.command(aliases=['ip', 'stat', 'mcip'])
	@commands.has_permissions(manage_messages=True)
	async def mcstatus(self, ctx: commands.Context):
		async with ctx.typing():
			await mc.serverstat(self)
			if self.online:
				embed = Embed(colour=0x00ff00)
				embed.add_field(name='Server IP', value=self.ip, inline=False)
				embed.add_field(name='Players Online', value=self.ppl_online, inline=False)
			else:
				embed = Embed(colour=0xff0000)
				embed.add_field(name='Server Offline', value=':(')
			embed.set_author(name='Minecraft Status', icon_url='https://cdn.discordapp.com/attachments/821765711848407091/878266221584322560/minecraft.png')
			embed.set_footer(text=f'Requested by: {ctx.message.author.display_name}')
			await ctx.send(embed=embed)

	@commands.command(aliases=['newserver', 'createserver'])
	@commands.has_permissions(manage_messages=True)
	async def mcnew(self, ctx: commands.Context, seed: Optional[int]):
		async with ctx.typing():
			await mc.serverstat(self)
			if self.online is False:
				msg = await ctx.send('Creating NEW WORLD...')
				system("start cmd /K cleanworld.bat")
				await sleep(2)
				copyfile('C:\\Users\\Andrew\\MCServer\\Speed\\server.properties.bak','C:\\Users\\Andrew\\MCServer\\Speed\\server.properties')
				if seed is not None:
					props= open("C:\\Users\\Andrew\\MCServer\\Speed\\server.properties", "a")
					props.write(f'\nlevel-seed={seed}')
					props.close()
				await sleep(2)
				await msg.edit(content='Starting NEW WORLD...')
				system("start cmd /K createworld.bat")
			else: return await ctx.send('Server is already up and running...')

def setup(client):
	client.add_cog(mc(client))