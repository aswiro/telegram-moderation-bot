from aiogram import Dispatcher
from aiogram_dialog import setup_dialogs as aiogram_dialog_setup

from .admin_dialog import admin_dialog
from .ads_dialog import ads_dialog
from .groups_dialog import groups_dialog
from .managers_dialog import managers_dialog
from .user_dialog import user_dialog


async def setup_dialogs(dp: Dispatcher) -> None:
    dp.include_routers(
        admin_dialog,
        user_dialog,
        groups_dialog,
        managers_dialog,
        ads_dialog,
    )
    aiogram_dialog_setup(dp)


__all__ = ["setup_dialogs"]
