import disnake
from disnake.ext import commands

from assistant import Client, colour_gen, long_date, relative_time


class Guild(commands.Cog):
    def __init__(self, client: Client):
        self.client = client

    @commands.slash_command(name="guild-info", description="Server info")
    @commands.guild_only()
    async def guild_info(self, inter: disnake.ApplicationCommandInteraction):
        guild = inter.guild
        embed = disnake.Embed(title=guild.name, color=colour_gen(guild.id))
        embed.description = guild.description if guild.description else ""
        embed.add_field(name="Guild Owner", value=guild.owner.mention)
        embed.add_field(name="Created On",
                        value=f"{long_date(guild.created_at)}\n{relative_time(guild.created_at)}")
        embed.add_field(name="Guild ID", value=f"`{guild.id}`")
        members = [member for member in guild.members if not member.bot]
        embed.add_field(name="No. of Members", value=len(members))
        online_members = [member for member in guild.members if member.raw_status != "offline" and not member.bot]
        embed.add_field(name="Members Online", value=len(online_members))
        bot_members = [member for member in guild.members if member.bot]
        embed.add_field(name="No. of Bots",
                        value=f'[{len(bot_members)}](https://discord.com/channels/{guild.id}/{inter.channel.id}\
                        \" {", ".join([member.display_name for member in bot_members])} \")')
        administrators = [m for m in guild.members if m.guild_permissions.administrator]
        embed.add_field(name="No of Administrators",
                        value=f'[{len(administrators)}](https://discord.com/channels/{guild.id}/{inter.channel.id}\
                        \" {", ".join([a.display_name for a in administrators])} \")')
        in_vc = [m for m in guild.members if m.voice]
        embed.add_field(name="No. of Members in VC",
                        value=f'[{len(in_vc)}](https://discord.com/channels/{guild.id}/{inter.channel.id}\
                        \" {", ".join([m.display_name for m in in_vc])} \")')
        await inter.response.send_message(embed=embed)


def setup(client):
    client.add_cog(Guild(client))
