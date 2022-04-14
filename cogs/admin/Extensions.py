from disnake.ext import commands

import assistant


class Extensions(commands.Cog):
    def __init__(self, client: assistant.Client):
        self.client = client
        self.logger = client.logger

    # Load Extension
    @commands.command(hidden=True)
    @commands.is_owner()
    async def load(self, ctx: commands.Context, extension) -> None:
        try:
            self.client.load_extension(f"cogs.{extension}")
        except Exception as e:
            await ctx.message.add_reaction("☠️")
            await ctx.send(f"{type(e).__name__}: {e}")
            self.logger.warning(f"Failed to load extension: cogs.{extension}")
        else:
            await ctx.message.add_reaction("✅")
            self.logger.info(f"Loaded extension: cogs.{extension}")

    # Unload Extension
    @commands.command(hidden=True)
    @commands.is_owner()
    async def unload(self, ctx: commands.Context, extension) -> None:
        try:
            self.client.unload_extension(f"cogs.{extension}")
        except Exception as e:
            await ctx.message.add_reaction("☠️")
            await ctx.send(f"{type(e).__name__}: {e}")
            self.logger.warning(f"Failed to unload extension: cogs.{extension}")
        else:
            await ctx.message.add_reaction("✅")
            self.logger.info(f"Unloaded extension: cogs.{extension}")

    # Reload Extension
    @commands.command(hidden=True)
    @commands.is_owner()
    async def reload(self, ctx: commands.Context, extension) -> None:
        try:
            self.client.reload_extension(f"cogs.{extension}")
        except Exception as e:
            await ctx.message.add_reaction("☠️")
            await ctx.send(f"{type(e).__name__}: {e}")
            self.logger.warning(f"Failed to reload extension: cogs.{extension}")
        else:
            await ctx.message.add_reaction("✅")
            self.logger.info(f"Reloaded extension: cogs.{extension}")


def setup(client):
    client.add_cog(Extensions(client))
