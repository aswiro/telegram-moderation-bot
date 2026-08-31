import asyncio

from bot.bot import start_bot
from logger import logger


async def main() -> None:
    logger.info("Starting bot...")
    await start_bot()


if __name__ == "__main__":
    asyncio.run(main())
