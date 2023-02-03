import disnake
from disnake.ext import commands

from assistant import Client


class Flames(commands.Cog):
    def __init__(self, client: Client):
        self.bot = client

    @commands.slash_command(name="flames", description="Calculate the flames between two names")
    async def flames(self, inter: disnake.ApplicationCommandInteraction,
                     name1: str = commands.Param(name="name1", description="First name"),
                     name2: str = commands.Param(name="name2", description="Second name",
                                                 default=lambda inter: inter.author.display_name),
                     ) -> None:
        o_name1, o_name2 = name1, name2
        name1, name2 = name1.lower(), name2.lower()

        if name1 == name2:
            await inter.response.send_message("You can't calculate flames between the same name!")
            return
        for i in name1:
            for j in name2:
                if i == j:
                    name1, name2 = name1.replace(i, "", 1), name2.replace(j, "", 1)
                    break
        total_chars = len(name1) + len(name2)
        flames = ["Friends", "Lovers", "Affection", "Marriage", "Enemies", "Siblings"]
        while len(flames) > 1:
            flames = flames[total_chars % len(flames):] + flames[:total_chars % len(flames) - 1]
        await inter.response.send_message(f"{o_name1} and {o_name2} are {flames[0]}")


def setup(bot):
    bot.add_cog(Flames(bot))
