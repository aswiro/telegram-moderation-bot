from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode
from fluent.runtime import FluentLocalization

from bot.dialogs.admin_dialog import AdminSG
from bot.dialogs.user_dialog import UserSG
from config import settings
from database.db import UnitOfWork
from database.models import User

router = Router()


@router.message(CommandStart())
async def start_command(
    message: Message,
    dialog_manager: DialogManager,
    uow: UnitOfWork,
    l10n: FluentLocalization,
):
    if not message.from_user:
        return

    tg_user = message.from_user
    user = await uow.users.get_by_telegram_id(tg_user.id)

    if not user:
        lang_code = tg_user.language_code if tg_user.language_code in {"ru", "en"} else "en"
        user = User(
            telegram_id=tg_user.id,
            username=tg_user.username,
            full_name=tg_user.full_name,
            language_code=lang_code,
        )
        await uow.users.add(user)
        await uow.commit()
    elif user.username != tg_user.username or user.full_name != tg_user.full_name:
        await uow.users.update(
            user.id,
            {"username": tg_user.username, "full_name": tg_user.full_name},
        )
        await uow.commit()

    state = dialog_manager.middleware_data.get("state")
    if state:
        await state.update_data(locale=user.language_code)

    if tg_user.id == settings.superadmin_id:
        await dialog_manager.start(AdminSG.main, mode=StartMode.RESET_STACK)
    else:
        await dialog_manager.start(UserSG.main, mode=StartMode.RESET_STACK)
