import disnake


def is_prob(guild: disnake.Guild) -> bool:
    """
    Check if a guild is a PROB
    """
    return guild.id == 368297437057515522


async def prob_hook(channel: [disnake.TextChannel | disnake.Thread | disnake.VoiceChannel]) -> disnake.Webhook:
    """
    Send a message to a Webhook
    """
    with open("data/prob.png", "rb") as file:
        avatar = file.read()
        file.close()
    webhooks = await channel.webhooks()
    for webhook in webhooks:
        if webhook.name == "PROB":
            return webhook
    return await channel.create_webhook(name="PROB", avatar=avatar)
