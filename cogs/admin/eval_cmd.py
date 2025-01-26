from time import time

import discord
from discord.ext import commands

from assistant import AssistantBot


class EvalCommand(commands.Cog):
    def __init__(self, bot: AssistantBot):
        self.bot = bot

    @staticmethod
    def resolve_variable(variable):
        if hasattr(variable, "__iter__"):
            var_length = len(list(variable))
            if (var_length > 100) and (not isinstance(variable, str)):
                return f"<a {type(variable).__name__} iterable with more than 100 values ({var_length})>"
            elif not var_length:
                return f"<an empty {type(variable).__name__} iterable>"

        if (not variable) and (not isinstance(variable, bool)):
            return f"<an empty {type(variable).__name__} object>"
        return (variable if (len(f"{variable}") <= 1000) else f"<a long {type(variable).__name__} object with the length of {len(f'{variable}'):,}>")

    @staticmethod
    def prepare(string):
        arr = (string.strip("```").replace("py\n", "").replace("python\n", "").split("\n"))
        if not arr[::-1][0].replace(" ", "").startswith("return"):
            arr[len(arr) - 1] = "return " + arr[::-1][0]
        return "".join(f"\n\t{i}" for i in arr)

    @commands.command(name="eval", hidden=True)
    @commands.is_owner()
    async def eval(self, ctx: commands.Context, *, code: str):
        silent = "-s" in code
        code = code.replace("-s", "")
        code = self.prepare(code)
        self.bot.logger.info(f"Eval command called in {ctx.channel}:\n{code}")
        args = {
            "disnake": discord,
            "import": __import__,
            "bot": self.bot,
            "None": None,
            "self": self,
            "ctx": ctx,
            "channel": ctx.channel,
            "author": ctx.author,
            "guild": ctx.guild,
            "message": ctx.message,
            "Embed": discord.Embed,
            "get": discord.utils.get,
            "find": discord.utils.find,
        }

        try:
            exec(f"async def func():{code}", args)
            a = time()
            response = await eval("func()", args)
            if silent or (response is None) or isinstance(response, discord.Message):
                del args, code
                return

            await ctx.send(f"```py\n{self.resolve_variable(response)}```" + f"`{type(response).__name__} | {round((time() - a) * 1000, 3)} ms` ")
        except Exception as e:
            await ctx.send(f"Error occurred:```\n{type(e).__name__}: {str(e)}```")

        del args, code, silent


async def setup(bot: AssistantBot):
    await bot.add_cog(EvalCommand(bot))
