import discord
from discord.ext import commands


def check_vc():
    async def predicate(ctx: commands.Context) -> bool:
        assert isinstance(ctx.author, discord.Member)
        assert ctx.guild is not None
        if ctx.author.voice is None:
            raise commands.CheckFailure("You must be in a voice channel.")
        assert ctx.author.voice.channel is not None
        permissions = ctx.author.voice.channel.permissions_for(ctx.guild.me)
        if not permissions.connect or not permissions.speak:
            raise commands.CheckFailure("I do not have the required permissions to join your voice channel.")
        return True

    return commands.check(predicate)


def check_same_vc():
    async def predicate(ctx: commands.Context) -> bool:
        assert isinstance(ctx.author, discord.Member)
        assert ctx.guild is not None
        assert ctx.author.voice is not None
        if ctx.guild.voice_client is None:
            raise commands.CheckFailure("I am not in a voice channel.")
        if ctx.guild.voice_client is not None and ctx.author.voice is not None:
            if ctx.guild.voice_client.channel == ctx.author.voice.channel:
                return True
        raise commands.CheckFailure("You must be in the same voice channel as me.")

    return commands.check(predicate)


async def owner_only(interaction: discord.Interaction):
    return await interaction.client.is_owner(interaction.user)
