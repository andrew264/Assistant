import aiohttp
import discord
from discord import app_commands, Status, ActivityType
from discord.ext import commands

from assistant import AssistantBot
from utils import owner_only


class Utilities(commands.Cog):
    def __init__(self, bot: AssistantBot):
        self.bot = bot

    @commands.command(name="echo", hidden=True)
    @commands.is_owner()
    @commands.guild_only()
    async def echo(self, ctx: commands.Context, *, message: str):
        """Echos the message back to the user."""
        await ctx.send(message,
                       embeds=ctx.message.embeds,
                       files=[await a.to_file() for a in ctx.message.attachments],
                       reference=ctx.message.reference, )
        await ctx.message.delete()

    @commands.hybrid_command(name="ping")
    async def ping(self, ctx: commands.Context):
        """Pong!"""
        await ctx.send(f"Pong! {round(self.bot.latency * 1000)}ms", ephemeral=True)

    @commands.command(description="Get External IPv4", hidden=True)
    @commands.is_owner()
    async def ip(self, ctx: commands.Context) -> None:
        # Get External IP
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.ipify.org') as response:
                ip = await response.text()
                await ctx.send(f"### External IPv4: ```{ip}```")

    @app_commands.command(name='setstatus', description='Set the bot\'s status', )
    # @app_commands.guilds(HOME_GUILD_ID)
    @app_commands.check(owner_only)
    async def set_status(self, inter: discord.Interaction, status: Status, activity_type: ActivityType, activity: str):
        await self.bot.change_presence(status=status, activity=discord.Activity(type=activity_type, name=activity))
        await inter.response.send_message(
            f"Status set to {str(status).capitalize()} {activity_type.name.capitalize()} {activity}",
            ephemeral=True)


async def setup(bot: AssistantBot):
    await bot.add_cog(Utilities(bot))
