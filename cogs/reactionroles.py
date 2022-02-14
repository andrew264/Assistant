# Imports
import disnake
from disnake.ext import commands


class ReactionRoles(commands.Cog):
    def __init__(self, client: disnake.Client):
        self.client = client
        self.role_message_id = 891793035959078932
        self.emoji_to_role = {
            disnake.PartialEmoji(name="🟥"): 891766305470971984,
            disnake.PartialEmoji(name="🟦"): 891766503219798026,
            disnake.PartialEmoji(name="🟩"): 891766413721759764,
            disnake.PartialEmoji(name="🟫"): 891782414412697600,
            disnake.PartialEmoji(name="🟧"): 891783123711455292,
            disnake.PartialEmoji(name="🟪"): 891782622374678658,
            disnake.PartialEmoji(name="🟨"): 891782804008992848,
        }

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: disnake.RawReactionActionEvent) -> None:
        """React to a message with an emoji to get a role."""
        if payload.message_id != self.role_message_id:
            return
        # ignore bots
        if payload.member.bot:
            return

        # fetch guild
        guild = self.client.get_guild(payload.guild_id)
        if guild is None:
            return

        channel = self.client.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)

        # filter out other emojis
        if payload.emoji not in self.emoji_to_role.keys():
            await message.remove_reaction(payload.emoji, payload.member)
            return

        # remove any colour roles
        role_ids = list(self.emoji_to_role.values())
        for role in payload.member.roles:
            if role.id != self.emoji_to_role[payload.emoji] and role.id in role_ids:
                await payload.member.remove_roles(role)

        # remove duplicate emojis
        for emoji in self.emoji_to_role.keys():
            if payload.emoji != emoji:
                try:
                    await message.remove_reaction(emoji, payload.member)
                except disnake.NotFound:
                    pass

        # fetch role
        role = guild.get_role(self.emoji_to_role[payload.emoji])
        if role is None:
            return

        # assign the role
        try:
            await payload.member.add_roles(role)
        except (disnake.HTTPException | disnake.Forbidden):
            pass

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: disnake.RawReactionActionEvent) -> None:
        if payload.message_id != self.role_message_id:
            return
        # filter out other emojis
        if payload.emoji not in self.emoji_to_role.keys():
            return

        # fetch member
        guild = self.client.get_guild(payload.guild_id)
        if guild is None:
            return
        member = await guild.fetch_member(payload.user_id)

        # just remove all colour roles for member
        for role in member.roles:
            if role.id in list(self.emoji_to_role.values()):
                await member.remove_roles(role)

    @commands.command()
    @commands.is_owner()
    async def reaction_roles(self, ctx: commands.Context) -> None:
        await ctx.message.delete()
        embed = disnake.Embed(title="Reaction Roles", colour=0xFFFFFF,
                              description="Claim a colour of your choice!", )
        msg = await ctx.send(embed=embed)
        for emoji in self.emoji_to_role.keys():
            await msg.add_reaction(emoji)


def setup(client):
    client.add_cog(ReactionRoles(client))
