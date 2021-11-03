# Imports
from time import time
from disnake.ext import commands
from disnake import Client
import disnake

class EvalCommand(commands.Cog):
    def __init__(self, client: Client):
        self.client = client
    
    def resolve_variable(self, variable):
        if hasattr(variable, "__iter__"):
            var_length = len(list(variable))
            if (var_length > 100) and (not isinstance(variable, str)):
                return f"<a {type(variable).__name__} iterable with more than 100 values ({var_length})>"
            elif (not var_length):
                return f"<an empty {type(variable).__name__} iterable>"
        
        if (not variable) and (not isinstance(variable, bool)):
            return f"<an empty {type(variable).__name__} object>"
        return (variable if (len(f"{variable}") <= 1000) else f"<a long {type(variable).__name__} object with the length of {len(f'{variable}'):,}>")
    
    def prepare(self, string):
        arr = string.strip("```").replace("py\n", "").replace("python\n", "").split("\n")
        if not arr[::-1][0].replace(" ", "").startswith("return"):
            arr[len(arr) - 1] = "return " + arr[::-1][0]
        return "".join(f"\n\t{i}" for i in arr)
    
    @commands.command(pass_context=True, aliases=['eval', 'exec', 'evaluate'])
    @commands.is_owner()
    async def _eval(self, ctx, *, code: str):
        silent = ("-s" in code)
        
        code = self.prepare(code.replace("-s", ""))
        args = {
            "disnake": disnake,
            "import": __import__,
            "self": self,
            "ctx": ctx,
            'channel': ctx.channel,
            'author': ctx.author,
            'guild': ctx.guild,
            'message': ctx.message,
            'Embed': disnake.Embed,
            'get': disnake.utils.get,
            'find': disnake.utils.find,
        }
        
        try:
            exec(f"async def func():{code}", args)
            a = time()
            response = await eval("func()", args)
            if silent or (response is None) or isinstance(response, disnake.Message):
                del args, code
                return
            
            await ctx.send(f"```py\n{self.resolve_variable(response)}````{type(response).__name__} | {round((time() - a)*1000,3)} ms`")
        except Exception as e:
            await ctx.send(f"Error occurred:```\n{type(e).__name__}: {str(e)}```")
        
        del args, code, silent
        
def setup(client):
	client.add_cog(EvalCommand(client))