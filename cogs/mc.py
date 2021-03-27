import discord
from discord.ext import commands
import urllib.request
import os
import shutil

from defs import checkIfProcessRunning

from discord.ext.commands import has_permissions

class mc(commands.Cog):

	def __init__(self,client):
		self.client = client

	# IP
	@commands.command(pass_context=True, brief='Get Server IP')
	@has_permissions(manage_messages=True)
	async def mcip(self, ctx):
		if checkIfProcessRunning():
			external_ip = urllib.request.urlopen('https://ident.me').read().decode('utf8')
			await ctx.send(f'{external_ip}:42069')
		else: return await ctx.send('Server isn\'t Running.')
	@commands.command(hidden=True)
	@mcip.error
	async def mcip_error(self, ctx, error):
		if isinstance(error, commands.MissingPermissions):
			await ctx.send('You have no Permission(s).')

	# check server is running
	@commands.command(pass_context=True, brief='Check Server Status.')
	async def mcstatus(self,ctx):
		if checkIfProcessRunning():
			await ctx.send('Server is Running.')
		else:
			await ctx.send('Server isn\'t Running.')

	# startup server
	@commands.command(pass_context=True, brief='Start Server. Required Arguments [vikki]')
	@has_permissions(manage_messages=True)
	async def mcstart(self,ctx,arg):
		if arg == 'vikki':
			if checkIfProcessRunning():
				return await ctx.send('A Server is already running.')
			else:
				os.system("start cmd /K vikki.bat")
				return await ctx.send('Server will start in 20 secs...')

	# startup server
	@commands.command(pass_context=True, brief='Create New Server. Required Arguments [SEED]')
	@has_permissions(manage_messages=True)
	async def mcnew(self,ctx,arg):
		if checkIfProcessRunning():
			return await ctx.send('A Server is already running.')
		try: 
			shutil.rmtree('C:\\Users\\Andrew\\MCServer\\Speed\\world')
			os.remove('C:\\Users\\Andrew\\MCServer\\Speed\\server.properties')
		except OSError as error: 
			print('World folder doesn\'t exist.')
		shutil.copyfile('C:\\Users\\Andrew\\MCServer\\Speed\\server.properties.bak','C:\\Users\\Andrew\\MCServer\\Speed\\server.properties')
		props= open("C:\\Users\\Andrew\\MCServer\\Speed\\server.properties", "a")
		props.write(f'\nlevel-seed={arg}')
		props.close()
		os.system("start cmd /K newworld.bat")
		return await ctx.send(f'Creating new world with seed: `{arg}`')


def setup(client):
	client.add_cog(mc(client))