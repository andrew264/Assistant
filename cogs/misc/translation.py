# Imports
import disnake
from disnake.ext import commands
from googletrans import Translator
from googletrans.models import Translated

from assistant import Client, colour_gen, getch_hook


class Translation(commands.Cog):
    def __init__(self, client: Client):
        self.client = client
        self.translator = Translator()

    @commands.message_command(name="Translate to English")
    @commands.guild_only()
    async def translate_to_english(self, inter: disnake.MessageCommandInteraction) -> None:
        msg = inter.target
        result: Translated = self.translator.translate(msg.content, dest="en")
        embed: disnake.Embed = disnake.Embed(title=f"{msg.author.display_name}'s message",
                                             color=colour_gen(msg.author.id))
        embed.add_field(name=f"Translated to 'en' from '{result.src}'", value=result.text, inline=False)
        await inter.response.send_message(embed=embed, ephemeral=True)

    @commands.slash_command(name="translate", description="Send a Translated Message")
    @commands.guild_only()
    async def translate(self, inter: disnake.MessageCommandInteraction,
                        message: str = commands.Param(description="Message to Translate"),
                        to: str = commands.Param(description="Select a Language",
                                                 choices=[disnake.OptionChoice(name="English", value="en"),
                                                          disnake.OptionChoice(name="Japanese", value="ja"),
                                                          disnake.OptionChoice(name="Tamil", value="ta"),
                                                          disnake.OptionChoice(name="Chinese", value="zh"),
                                                          disnake.OptionChoice(name="French", value="fr"),
                                                          disnake.OptionChoice(name="German", value="de"),
                                                          disnake.OptionChoice(name="Spanish", value="es"),
                                                          disnake.OptionChoice(name="Korean", value="ko"),
                                                          disnake.OptionChoice(name="Russian", value="ru"),
                                                          disnake.OptionChoice(name="Swedish", value="sv"),
                                                          disnake.OptionChoice(name="Hindi", value="hi"),
                                                          ])) -> None:
        await inter.response.send_message(f"Translating `{message}` to **{to}**", ephemeral=True)
        result: Translated = self.translator.translate(message, dest=to)
        webhook: disnake.Webhook = await getch_hook(inter.channel)
        await webhook.send(content=result.text,
                           username=inter.author.display_name,
                           avatar_url=inter.author.display_avatar.url)


def setup(client: Client):
    client.add_cog(Translation(client))
