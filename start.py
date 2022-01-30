# Imports
from os import listdir

from disnake import Intents
from disnake.ext import commands

from EnvVariables import TOKEN, Owner_ID

# Client
client = commands.Bot(
    command_prefix=commands.when_mentioned_or("."),
    intents=Intents.all(),
    help_command=None,
    case_insensitive=True,
    test_guilds=[821758346054467584, 914122845678870539],
    owner_id=Owner_ID,
    description="Andrew's Assistant",
)


# Load Extension
@client.command(hidden=True)
@commands.is_owner()
async def load(ctx: commands.Context, extension) -> None:
    try:
        client.load_extension(f"cogs.{extension}")
    except Exception as e:
        await ctx.message.add_reaction("☠️")
        await ctx.send(f"{type(e).__name__}: {e}")
    else:
        await ctx.message.add_reaction("✅")


# Unload Extension
@client.command(hidden=True)
@commands.is_owner()
async def unload(ctx: commands.Context, extension) -> None:
    try:
        client.unload_extension(f"cogs.{extension}")
    except Exception as e:
        await ctx.message.add_reaction("☠️")
        await ctx.send(f"{type(e).__name__}: {e}")
    else:
        await ctx.message.add_reaction("✅")


# Reload Extension
@client.command(hidden=True)
@commands.is_owner()
async def reload(ctx: commands.Context, extension) -> None:
    try:
        client.reload_extension(f"cogs.{extension}")
    except Exception as e:
        await ctx.message.add_reaction("☠️")
        await ctx.send(f"{type(e).__name__}: {e}")
    else:
        await ctx.message.add_reaction("✅")


for filename in listdir("./cogs"):
    if filename.endswith(".py"):
        client.load_extension(f"cogs.{filename[:-3]}")

client.run(TOKEN)
