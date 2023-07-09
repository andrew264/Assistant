import discord
from discord.ext import commands


class CommandErrorHandler(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        # This prevents any commands with local handlers being handled here in on_command_error.
        if hasattr(ctx.command, 'on_error'):
            return

        # This prevents any cogs with an overwritten cog_command_error being handled here.
        cog = ctx.cog
        if cog:
            if cog._get_overridden_method(cog.cog_command_error) is not None:
                return

        ignored = (commands.CommandNotFound,)
        error = getattr(error, 'original', error)

        if isinstance(error, ignored):
            return

        if isinstance(error, commands.DisabledCommand):
            await ctx.send(f'{ctx.command} has been disabled.')

        elif isinstance(error, commands.NoPrivateMessage):
            try:
                await ctx.author.send(f'{ctx.command} can not be used in Private Messages.')
            except discord.HTTPException:
                pass

        elif isinstance(error, (commands.MissingPermissions, commands.BotMissingPermissions)):
            try:
                await ctx.send(content=str(error))
            except discord.HTTPException:
                pass

        elif isinstance(error, commands.NSFWChannelRequired):
            try:
                await ctx.send(f'{ctx.command} command can only be used in NSFW channels.')
            except discord.HTTPException:
                pass

        elif isinstance(error, commands.CheckFailure):
            try:
                await ctx.send(content=f"{error}")
            except discord.HTTPException:
                pass

        elif isinstance(error, commands.NotOwner):
            try:
                await ctx.send(f'{ctx.command} can only be used by the owner.')
            except discord.HTTPException:
                pass

        elif isinstance(error, commands.UserInputError):
            try:
                await ctx.send(f"Error: Invalid `{', '.join(error.args)}` Argument.")
            except discord.HTTPException:
                pass

        elif isinstance(error, commands.MemberNotFound):
            try:
                await ctx.send(f"🚫 Member not found.")
            except discord.HTTPException:
                pass

        else:
            self.bot.logger.error(f'Ignoring exception in command {ctx.command}:', exc_info=error)

            await ctx.send(f'```py\n{error}```')


async def setup(bot):
    await bot.add_cog(CommandErrorHandler(bot))
