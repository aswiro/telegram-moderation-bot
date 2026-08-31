import random

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from database.db import UnitOfWork
from logger import logger

_last_sent_ad_ids: list[int] = []


async def send_random_ad(bot: Bot) -> None:
    global _last_sent_ad_ids

    async with UnitOfWork() as uow:
        ads = await uow.ads.get_all()
        groups = await uow.groups.get_all()

        if not ads or not groups:
            return

        available = [ad for ad in ads if ad.id not in _last_sent_ad_ids] or ads
        ad = random.choice(available)

        _last_sent_ad_ids.append(ad.id)
        if len(_last_sent_ad_ids) >= len(ads):
            _last_sent_ad_ids = []

        for group in groups:
            try:
                manager = (
                    await uow.users.get_by_id(group.manager_id)
                    if group.manager_id
                    else None
                )
                keyboard = None
                if manager and manager.username:
                    keyboard = InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                InlineKeyboardButton(
                                    text="Contact manager",
                                    url=f"https://t.me/{manager.username}",
                                )
                            ]
                        ]
                    )

                if ad.content_type == "photo":
                    await bot.send_photo(
                        group.telegram_id,
                        ad.file_id,
                        caption=ad.text,
                        reply_markup=keyboard,
                    )
                elif ad.content_type == "video":
                    await bot.send_video(
                        group.telegram_id,
                        ad.file_id,
                        caption=ad.text,
                        reply_markup=keyboard,
                    )
                else:
                    await bot.send_message(
                        group.telegram_id,
                        ad.text or "",
                        reply_markup=keyboard,
                    )
            except Exception as exc:
                logger.error("Scheduled delivery failed for group {}: {}", group.id, exc)


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(jobstores={"default": MemoryJobStore()})
    scheduler.add_job(
        send_random_ad,
        "interval",
        minutes=30,
        args=[bot],
        replace_existing=True,
        id="send_random_ad",
    )
    return scheduler
