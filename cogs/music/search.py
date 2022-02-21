from typing import Optional

import disnake
from disnake.ext import commands
from lavalink import DefaultPlayer as Player

import assistant


class Search(commands.Cog):
    def __init__(self, client: assistant.Client):
        self.client = client
        self.lavalink = client.lavalink

    @commands.command(name="search", aliases=["s", "yt"])
    async def search(self, ctx: commands.Context, *, query: str) -> None:
        """Search YouTube with query and add it to Player Queue."""
        player: Player = self.lavalink.player_manager.create(ctx.guild.id, endpoint=str(ctx.guild.region))
        client = self.client

        await ctx.message.delete(delay=5)

        results = await player.node.get_tracks(f"ytsearch:{query}")
        if not results or not results["tracks"]:
            await ctx.send("No results found.", delete_after=15)
            return

        tracks: list = results["tracks"][:5]

        class Select(disnake.ui.Select):
            def __init__(self):
                options = [disnake.SelectOption(label=track['title'], value=track['uri']) for track in tracks]
                super().__init__(placeholder="Select a song", options=options,
                                 min_values=1, max_values=1, )

            async def callback(self, interaction: disnake.MessageInteraction):
                if interaction.author == ctx.author:
                    await ctx.invoke(client.get_command("play"), query=self.values[0])
                    await interaction.message.edit(content="kthxbye", embed=None, view=None, delete_after=10)
                else:
                    await interaction.send(content="You can't select a song.", ephemeral=True)

        class DropDown(disnake.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
                self.add_item(Select())
                self.msg: Optional[disnake.Message] = None

            async def on_timeout(self) -> None:
                self.stop()
                await self.msg.delete()

        embed = disnake.Embed(title=f"Search Results for `{query}`", color=0x00ff00)
        embed.description = "\n".join(f"`{i + 1}.` [{t['title']}]({t['uri']})" for i, t in enumerate(tracks))
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
        view = DropDown()
        view.msg = await ctx.send(embed=embed, view=view)

    # Checks
    @search.before_invoke
    async def check_play(self, ctx: commands.Context) -> None:
        if ctx.author.voice is None:
            raise commands.CheckFailure("You are not connected to a voice channel.")
        if ctx.voice_client is not None and ctx.author.voice is not None:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                raise commands.CheckFailure("You must be in same VC as Bot.")
        permissions = ctx.author.voice.channel.permissions_for(ctx.me)
        if not permissions.connect or not permissions.speak:
            raise commands.CheckFailure('Missing `CONNECT` and `SPEAK` permissions.')


def setup(client: assistant.Client):
    client.add_cog(Search(client))
