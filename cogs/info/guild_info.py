import discord
from discord import utils
from discord.ext import commands

from assistant import AssistantBot


class GuildInfo(commands.Cog):
    def __init__(self, bot: AssistantBot):
        self.bot = bot

    @commands.hybrid_command(name="guild-info", aliases=["guild", "server"], description="Shows guild stats/info")
    @commands.guild_only()
    async def guild_info(self, ctx: commands.Context):
        assert ctx.guild
        guild = ctx.guild
        embed = discord.Embed(title=guild.name, color=discord.Color.blurple())
        embed.description = guild.description if guild.description else ""
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        embed.add_field(name="Owner", value=guild.owner.mention if guild.owner else "None")
        embed.add_field(name="Created on", value=f"{utils.format_dt(guild.created_at, style='F')}\n"
                                                 f"{utils.format_dt(guild.created_at, style='R')}")
        members = [member for member in guild.members if not member.bot]
        embed.add_field(name="Total Members", value=f"{len(members)}")
        online_members = [member for member in members if member.status != discord.Status.offline]
        embed.add_field(name="Online Members", value=f"{len(online_members)}")
        embed.add_field(name="Total Bots", value=f"{len([member for member in guild.members if member.bot])}")
        embed.add_field(name="Total Text Channels", value=f"{len(guild.text_channels)}")
        embed.add_field(name="Total Voice Channels", value=f"{len(guild.voice_channels)}")
        embed.add_field(name="No. of Roles", value=f"{len(guild.roles)}")
        embed.add_field(name="No. of Emojis", value=f"{len(guild.emojis)}")
        if guild.premium_subscription_count:
            embed.add_field(name="Boosts", value=f"{guild.premium_subscription_count}")
        embed.add_field(name="Total Admins", value=f"{len([member for member in guild.members if member.guild_permissions.administrator])}")
        in_vc = [member for member in guild.members if member.voice]
        if in_vc:
            embed.add_field(name="Members in VC", value=f"{len(in_vc)}")
        embed.set_footer(text=f"ID: {guild.id}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)


async def setup(bot: AssistantBot):
    await bot.add_cog(GuildInfo(bot))
