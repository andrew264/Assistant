import traceback

import disnake
from disnake import Embed, Color
from disnake.ext import commands

import assistant


def fancy_traceback(exc: Exception) -> str:
    text = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    return f"```py\n{text[-4086:]}\n```"


class ErrorHandler(commands.Cog):
    def __init__(self, client: assistant.Client):
        self.client = client

    # Unknown commands
    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        self.client.logger.error(f"Command `{ctx.command.name}` failed due to `{error}`")
        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send(error, delete_after=60)
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send(error, delete_after=60)
        elif isinstance(error, commands.NotOwner):
            await ctx.send("🚫 You can't do that.")
        elif isinstance(error, commands.UserInputError):
            await ctx.send(f"Error: Invalid {error.args[0]} Argument.")
        elif isinstance(error, commands.CheckFailure):
            await ctx.send(f"***{error}***")
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send(f"🚫 Member not found.")
        else:
            await ctx.send(f"An unknown error occurred")
            embed = Embed(title=f"Command `{ctx.command}` failed due to `{error}`",
                          description=fancy_traceback(error), color=Color.red(), )
            await self.client.log(embed=embed)

    # slash errors
    @commands.Cog.listener()
    async def on_slash_command_error(self, inter: disnake.ApplicationCommandInteraction,
                                     error: commands.CommandError) -> None:
        self.client.logger.error(f"Command `{inter.application_command.name}` failed due to `{error}`")
        if isinstance(error, commands.NotOwner):
            await inter.response.send_message("🚫 You can't do that.", ephemeral=True)
        elif isinstance(error, commands.MissingPermissions) or isinstance(error, commands.BotMissingPermissions):
            await inter.response.send_message(error, ephemeral=True)
        elif isinstance(error, commands.NoPrivateMessage):
            await inter.response.send_message("🚫 You can't do that in DMs.")
        elif isinstance(error, commands.MemberNotFound):
            await inter.response.send_message(f"🚫 Member not found.")
        elif isinstance(error, commands.CheckFailure):
            await inter.response.send_message(f"***{error}***")
        else:
            try:
                await inter.response.send_message(f"An unknown error occurred")
            except disnake.InteractionResponded:
                await inter.edit_original_message(content=f"An unknown error occurred")
            embed = Embed(title=f"Command `{inter.application_command.name}` failed due to `{error}`",
                          description=fancy_traceback(error), color=Color.red(), )
            await self.client.log(embed=embed)

    # Message Context Error
    @commands.Cog.listener()
    async def on_message_command_error(self, inter: disnake.ApplicationCommandInteraction,
                                       error: commands.CommandError) -> None:
        self.client.logger.error(f"Command `{inter.application_command.name}` failed due to `{error}`")
        if isinstance(error, commands.NotOwner):
            await inter.response.send_message("🚫 You can't do that.", ephemeral=True)
        elif isinstance(error, commands.MissingPermissions):
            await inter.response.send_message(error, ephemeral=True)
        elif isinstance(error, commands.NoPrivateMessage):
            await inter.response.send_message("🚫 You can't do that in DMs.")
        elif isinstance(error, commands.MemberNotFound):
            await inter.response.send_message(f"🚫 Member not found.")
        else:
            await inter.response.send_message(f"An unknown error occurred")
            embed = Embed(title=f"Command `{inter.application_command.name}` failed due to `{error}`",
                          description=fancy_traceback(error), color=Color.red(), )
            await self.client.log(embed=embed)

    # User Context Error
    @commands.Cog.listener()
    async def on_user_command_error(self, inter: disnake.ApplicationCommandInteraction,
                                    error: commands.CommandError) -> None:
        self.client.logger.error(f"Command `{inter.application_command.name}` failed due to `{error}`")
        if isinstance(error, commands.NotOwner):
            await inter.response.send_message("🚫 You can't do that.", ephemeral=True)
        elif isinstance(error, commands.MissingPermissions):
            await inter.response.send_message(error, ephemeral=True)
        elif isinstance(error, commands.NoPrivateMessage):
            await inter.response.send_message("🚫 You can't do that in DMs.")
        elif isinstance(error, commands.MemberNotFound):
            await inter.response.send_message(f"🚫 Member not found.")
        else:
            await inter.response.send_message(f"An unknown error occurred")
            embed = Embed(title=f"Command `{inter.application_command.name}` failed due to `{error}`",
                          description=fancy_traceback(error), color=Color.red(), )
            await self.client.log(embed=embed)


def setup(client):
    client.add_cog(ErrorHandler(client))
