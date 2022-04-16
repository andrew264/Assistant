from disnake.ext import commands

from assistant import Client


class ToggleChatbot(commands.Cog):
    def __init__(self, client: Client):
        self.client = client

    @commands.command(aliases=['tweb'])
    @commands.is_owner()
    async def toggle_webs(self, ctx: commands.Context):
        is_webs_loaded = self.client.extensions.get('cogs.tasks.andrew_webs')
        if is_webs_loaded:
            self.client.unload_extension('cogs.tasks.andrew_webs')
            await ctx.send('Andrew_webs disabled')
        else:
            self.client.load_extension('cogs.tasks.andrew_webs')
            await ctx.send('Andrew_webs enabled')

    @commands.command(aliases=['tcb'])
    @commands.is_owner()
    async def toggle_chatbot(self, ctx: commands.Context):
        is_chatbot_loaded = self.client.extensions.get('cogs.chatbot.chat')
        if is_chatbot_loaded:
            self.client.unload_extension('cogs.chatbot.chat')
            await ctx.send('Chatbot disabled')
        else:
            self.client.load_extension('cogs.chatbot.chat')
            await ctx.send('Chatbot enabled')


def setup(client):
    client.add_cog(ToggleChatbot(client))
