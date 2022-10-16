import typing

import disnake


async def getch_hook(
        channel: typing.Union[disnake.TextChannel, disnake.Thread, disnake.VoiceChannel]) -> disnake.Webhook:
    """
    Send a message to a Webhook
    """
    with open("data/prob.png", "rb") as file:
        avatar = file.read()
        file.close()
    webhooks = await channel.webhooks()
    for webhook in webhooks:
        if webhook.name == "Assistant":
            return webhook
    return await channel.create_webhook(name="Assistant", avatar=avatar)
