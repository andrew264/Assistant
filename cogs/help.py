import discord.ext.commands as commands
from discord import Embed

class help(commands.Cog):
    def __init__(self,client):
        self.client = client

    @commands.command(aliases=['h'])
    async def help(self, ctx, args=''):
        if args=='':
            embed=Embed(title='Help',colour=0x00cd00,description="Use `.help [module]` to get even more help")
            embed.add_field(name='music',value='yep i can play music too',inline=False)
            embed.add_field(name='minecraft',value='Switch on server & get IP address',inline=False)
            embed.add_field(name='dialogues',value='Play some Dialogues',inline=False)
            embed.add_field(name='misc',value='Even more Commands',inline=False)
            await ctx.send(embed=embed)
        elif args=='music':
            embed=Embed(title='Music Commands',colour=0x00cd00,description='I can play musics too.')
            embed.add_field(name='Play',value='`.play|.p` [**Title**|**URL**]',inline=True)
            embed.add_field(name='Pause',value='`.pause` to pause the song',inline=True)
            embed.add_field(name='Now Playing',value='`.np` to get current song',inline=True)
            embed.add_field(name='Stop',value='`.stop` to stop the song',inline=True)
            embed.add_field(name='Skip',value='`.skip` or `.skip <song#>` to skip songs',inline=True)
            embed.add_field(name='Queue',value='`.queue|.q` to list the songs in Queue',inline=True)
            embed.add_field(name='Loop',value='`.loop` to loop all songs in Queue',inline=True)
            await ctx.send(embed=embed)
        elif args=='mc' or args=='minecraft':
            embed=Embed(title='Minecraft',colour=0x00cd00,description='Minecraft related stuff')
            embed.add_field(name='Start Server',value='`.mcstart` to start the server',inline=False)
            embed.add_field(name='Server Status',value='`.mcstatus` to get server status',inline=False)
            embed.add_field(name='Create New Server',value='`.mcnew [SEED]` to create a new server',inline=False)
            embed.add_field(name='Get IP Address',value='`.mcip` to get ip address',inline=False)
            await ctx.send(embed=embed)
        elif args=='d' or args=='dialogue':
            embed=Embed(title='Dialogues',colour=0x00cd00,description='Some Dialogues lol')
            embed.add_field(name='Dialogues',value='`.d [list|rand|name]` list, play random, play specfic ones')
            await ctx.send(embed=embed)
        elif args=='misc':
            embed=Embed(title='Misc',colour=0x00cd00,description='Even more commands')
            embed.add_field(name='Delete Messages',value='`.clear [No.ofMessages]` to delete messages',inline=False)
            embed.add_field(name='Ping',value='`.ping` to get bot latency',inline=False)
            await ctx.send(embed=embed)
        else:
            await ctx.send('I don\'t know what you are talking about.')



def setup(client):
	client.add_cog(help(client))