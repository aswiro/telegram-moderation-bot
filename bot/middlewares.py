from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from database.db import UnitOfWork


class UoWMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        async with UnitOfWork() as uow:
            data["uow"] = uow
            return await handler(event, data)


class LocalizationMiddleware(BaseMiddleware):
    def __init__(self, localization_loader):
        super().__init__()
        self.localization_loader = localization_loader

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        lang = "en"
        state = data.get("state")
        state_data = await state.get_data() if state else {}

        if "locale" in state_data:
            lang = state_data["locale"]
        else:
            uow = data.get("uow")
            user = getattr(event, "from_user", None)
            if uow and user:
                db_user = await uow.users.get_by_telegram_id(user.id)
                if db_user:
                    lang = db_user.language_code
                    if state:
                        await state.update_data(locale=lang)

        data["l10n"] = self.localization_loader(lang)
        return await handler(event, data)
