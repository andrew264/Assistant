import disnake
from disnake.ext import commands

from assistant import Client


class Flames(commands.Cog):
    def __init__(self, client: Client):
        self.client = client

    @commands.slash_command(name="flames", description="Calculate the flames between two names")
    async def flames(self, inter: disnake.ApplicationCommandInteraction,
                     name1: str = commands.Param(name="name1", description="First name"),
                     name2: str = commands.Param(name="name2", description="Second name",
                                                 default=lambda inter: inter.author.display_name),
                     ) -> None:
        o_name1, o_name2 = name1, name2
        name1, name2 = name1.lower(), name2.lower()
        name1.replace(" ", "")
        name2.replace(" ", "")

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
            rem_index = (total_chars % len(flames)) - 1
            if rem_index >= 0:
                left = flames[:rem_index]
                right = flames[rem_index + 1:]
                flames = right + left
            else:
                flames = flames[:len(flames) - 1]
        self.client.logger.info(f"{str(inter.author)} did FLAMES for {o_name1} & {o_name2} -> {flames[0]}")
        await inter.response.send_message(f"FLAMES for _{o_name1}_ and _{o_name2}_ is `{flames[0]}`")


def setup(client: Client):
    client.add_cog(Flames(client))
