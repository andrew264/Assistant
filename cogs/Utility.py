# Imports
from typing import Optional

import aiohttp
import disnake
from disnake.ext import commands
from disnake.ext.commands import Param

import assistant


class Utility(commands.Cog):
    def __init__(self, client: assistant.Client):
        self.client = client

    # echo
    @commands.command(hidden=True)
    @commands.is_owner()
    @commands.guild_only()
    async def echo(self, ctx: commands.Context, *, args) -> None:
        await ctx.send(args)
        await ctx.message.delete()

    # ping
    @commands.slash_command(description="Get Bot's Latency")
    async def ping(self, inter: disnake.ApplicationCommandInteraction) -> None:
        await inter.response.send_message(f"Client Latency: {round(self.client.latency * 1000)}  ms")

    # Fetch external IPv4
    @commands.command(description="Get External IPv4")
    @commands.is_owner()
    async def ip(self, ctx: commands.Context) -> None:
        # Get External IP
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.ipify.org') as response:
                ip = await response.text()
        await ctx.send(f"External IPv4: {ip}")

    # Set Status
    State = commands.option_enum({"Online": "online",
                                  "Idle": "idle",
                                  "Do not Disturb": "dnd",
                                  "Invisible": "offline", })
    ActType = commands.option_enum({"Playing": "0", "Streaming": "1",
                                    "Listening": "2", "Watching": "3"})

    @commands.slash_command(description="Set Bot's Activity")
    @commands.is_owner()
    async def status(self, inter: disnake.ApplicationCommandInteraction,
                     state: State = Param(description="Set Bot's Status"),
                     activity: ActType = Param(description="Set Bot's Activity Type"),
                     name: str = Param(description="Set Bot's Activity Name", default="yall Homies"), ) -> None:
        await self.client.change_presence(status=disnake.Status(state),
                                          activity=disnake.Activity(type=disnake.ActivityType(int(activity)),
                                                                    name=name), )
        await inter.edit_original_message(content=f"Status set to `{disnake.Status(state).name.capitalize()}`|\
        `{disnake.ActivityType(int(activity)).name.title()}: {name}`", )

    # clear
    @commands.command(aliases=["delete"])
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def clear(self, ctx: commands.Context, user: Optional[disnake.User],
                    no_of_msgs: int = 5, contains: str = "") -> None:
        if no_of_msgs > 420:
            await ctx.reply(f"No")
            return
        await ctx.message.delete()
        if user and contains:

            def check(msg: disnake.Message) -> bool:
                return msg.author.id == user.id

            await ctx.channel.purge(limit=no_of_msgs, check=check)
            await ctx.send(f"`{ctx.author.display_name}` deleted `{user.display_name}'s` `{no_of_msgs}` message(s).",
                           delete_after=30, )
        elif user is None and contains:
            def check(msg: disnake.Message) -> bool:
                return contains.lower() in msg.content.lower()

            await ctx.channel.purge(limit=no_of_msgs, check=check)
            await ctx.send(f"`{ctx.author.display_name}` deleted messages containing {contains}.", delete_after=30, )
        else:
            await ctx.channel.purge(limit=no_of_msgs)
            await ctx.send(f"`{ctx.author.display_name}` deleted `{no_of_msgs}` message(s).", delete_after=30)

    # Context Delete
    @commands.message_command(name="Delete till HERE")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def ContextClear(self, inter: disnake.MessageCommandInteraction) -> None:
        await inter.response.defer(ephemeral=True)
        await inter.channel.purge(after=inter.target)
        await inter.edit_original_message(
            content=f"`{inter.author.display_name}` deleted messages till `{inter.target.author.display_name}'s` message", )

    @commands.command(aliases=["yeet"])
    @commands.guild_only()
    @commands.is_owner()
    async def purge_user(self, ctx: commands.Context, user_id: Optional[int], *, strings: Optional[str]) -> None:
        await ctx.message.delete()
        if user_id is None and strings is None:
            await ctx.send("Enter UserID or give a string to search for")
            return
        msgs_to_delete: list[disnake.Message] = []
        string_list: list[str] = [string.lower() for string in list(strings.split(","))] if strings else []
        if user_id:
            string_list.append(str(user_id))
        await ctx.send(f"Fetching messages from {ctx.channel.mention}", delete_after=30)
        messages: list[disnake.Message] = await ctx.channel.history(limit=69420).flatten()
        await ctx.send(f"Fetched {len(messages)} messages", delete_after=30)
        for message in messages:
            if user_id and message.author.id == user_id:
                print(f"{str(message.author)}: {message.content}")
                msgs_to_delete.append(message)
                continue
            if any(string in str(message.author).lower() for string in string_list) \
                    or any(string in message.content.lower() for string in string_list):
                print(f"{message.author.name}: {message.content}")
                msgs_to_delete.append(message)
                continue
            if not message.embeds:
                continue
            for embed in message.embeds:
                if any(string in str(embed.title).lower() for string in string_list) \
                        or any(string in str(embed.description).lower() for string in string_list) \
                        or any(string in str(embed.author.name).lower() for string in string_list) \
                        or any(string in str(embed.footer.text).lower() for string in string_list):
                    print(
                        f"{message.author.name}:{embed.title}:{embed.author.name}:{embed.description}:{embed.footer.text}")
                    msgs_to_delete.append(message)
                    continue
                for field in embed.fields:
                    if any(string in field.value.lower() for string in string_list) \
                            or any(string in field.name.lower() for string in string_list):
                        print(f"{message.author.name}: {field.name}:{field.value}")
                        msgs_to_delete.append(message)
                        continue
        try:
            for i, msg in enumerate(msgs_to_delete):
                await msg.delete()
                print(f"{i + 1}/{len(msgs_to_delete)} - {round((i + 1) / len(msgs_to_delete) * 100, 2)}% deleted")
        except Exception as e:
            print(e)
            pass
        print(f"Deleted {len(msgs_to_delete)} messages in #{ctx.channel.name}")
        await ctx.send(f"Deleted {len(msgs_to_delete)} messages.", delete_after=30)


def setup(client):
    client.add_cog(Utility(client))
