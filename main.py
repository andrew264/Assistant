import asyncio

import discord
import wavelink

from assistant import AssistantBot
from config import PREFIX, DISCORD_TOKEN, OWNER_ID, STATUS, ACTIVITY_TYPE, ACTIVITY_TEXT

intent = discord.Intents.all()

bot = AssistantBot(
    command_prefix=PREFIX,
    owner_id=OWNER_ID,
    intents=intent,
    help_command=None,
    case_insensitive=True,
    status=STATUS,
    activity=discord.Activity(type=ACTIVITY_TYPE, name=ACTIVITY_TEXT),
)


async def main():
    if DISCORD_TOKEN is None:
        print("No token provided. Please provide a token in config.toml")
        exit(1)
    async with bot:
        bot.logger.info("[STARTING] Assistant...")
        await bot.start(DISCORD_TOKEN)


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(main())
    except (KeyboardInterrupt, SystemExit):
        bot.logger.info("[RECEIVED] Keyboard Interrupt. Exiting...")
    finally:
        for task in asyncio.all_tasks(loop):
            task.cancel()
        loop.run_until_complete(wavelink.Pool.close())
        loop.run_until_complete(bot.close())
        loop.close()
