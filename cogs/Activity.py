import disnake
from disnake.ext import commands

import assistant
from assistant import is_prob, prob_hook

activities = [
    disnake.OptionChoice("YouTube Watch Together", str(disnake.PartyType.watch_together.value)),
    disnake.OptionChoice("Sketch Heads", str(disnake.PartyType.sketch_heads.value)),
    disnake.OptionChoice("Word Snacks", str(disnake.PartyType.word_snack.value)),
    disnake.OptionChoice("Betrayal.io", str(disnake.PartyType.betrayal.value)),
    disnake.OptionChoice("Fishington.io", str(disnake.PartyType.fishing.value)),
]


class Activity(commands.Cog):
    def __init__(self, client: assistant.Client):
        self.client = client

    @commands.slash_command(name="activity")
    @commands.guild_only()
    @commands.bot_has_permissions(create_instant_invite=True)
    async def activity(self, inter: disnake.ApplicationCommandInteraction,
                       activity=commands.Param(description="Select an activity type", choices=activities,
                                               default=str(disnake.PartyType.youtube.value))) -> None:
        """Start an Activity in Voice Channel"""
        if inter.author.voice is None:
            await inter.response.send_message("You must be in a voice channel to use this command.")
            return
        invite = await inter.author.voice.channel.create_invite(target_type=disnake.InviteTarget.embedded_application,
                                                                target_application=disnake.PartyType(int(activity)),
                                                                max_age=300)
        if is_prob(inter.guild):
            await inter.response.send_message("Creating Invite", ephemeral=True)
            hook = await prob_hook(inter.channel)
            await hook.send(content=f"Invite link: {invite}", delete_after=300)
            return
        await inter.response.send_message(f"Invite link: {invite}", delete_after=300)


def setup(client):
    client.add_cog(Activity(client))
