import asyncio

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import DefaultKeyBuilder, RedisStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from redis.asyncio import Redis

from bot.dialogs import setup_dialogs
from bot.handlers.start import router as start_router
from bot.localization import get_localization
from bot.middlewares import LocalizationMiddleware, UoWMiddleware
from config import settings
from database.db import create_tables
from logger import logger
from scheduler import setup_scheduler


async def start_bot() -> None:
    redis = Redis(host=settings.redis_host, port=settings.redis_port)
    storage = RedisStorage(
        redis=redis,
        key_builder=DefaultKeyBuilder(with_bot_id=True, with_destiny=True),
    )

    bot = Bot(token=settings.bot_token)
    dp = Dispatcher(storage=storage)

    dp.update.middleware(UoWMiddleware())
    dp.message.outer_middleware(LocalizationMiddleware(get_localization))
    dp.callback_query.outer_middleware(LocalizationMiddleware(get_localization))

    await setup_dialogs(dp)
    dp.include_router(start_router)

    scheduler = setup_scheduler(bot)
    scheduler.start()

    logger.info("Ensuring database tables exist...")
    await create_tables()

    if settings.use_webhook:
        if not settings.webhook_base or not settings.webhook_secret:
            raise RuntimeError("WEBHOOK_BASE and WEBHOOK_SECRET are required in webhook mode")

        app = web.Application()
        SimpleRequestHandler(
            dispatcher=dp,
            bot=bot,
            secret_token=settings.webhook_secret,
        ).register(app, path=settings.webhook_path)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(
            runner,
            host=settings.webapp_host,
            port=settings.webapp_port,
        )
        await site.start()
        await bot.set_webhook(
            url=f"{settings.webhook_base}{settings.webhook_path}",
            secret_token=settings.webhook_secret,
        )

        try:
            await asyncio.Event().wait()
        finally:
            await bot.delete_webhook()
            await runner.cleanup()
            scheduler.shutdown()
            await bot.session.close()
            await redis.aclose()
    else:
        try:
            logger.info("Bot started in polling mode")
            await dp.start_polling(bot)
        finally:
            scheduler.shutdown()
            await bot.session.close()
            await redis.aclose()
