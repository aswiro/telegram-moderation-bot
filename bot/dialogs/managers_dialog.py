from dataclasses import dataclass
from typing import Any

from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, StartMode, Window
from aiogram_dialog.widgets.kbd import Button, ScrollingGroup, Select
from aiogram_dialog.widgets.text import Format
from fluent.runtime import FluentLocalization

from bot.dialogs.states import AdminSG, ManagersSG
from config import settings
from database.db import UnitOfWork
from database.models import User as DBUser
from logger import logger


@dataclass
class AdminView:
    telegram_id: int
    name: str


async def get_groups(uow: UnitOfWork, l10n: FluentLocalization, **kwargs):
    return {
        "groups": await uow.groups.get_all(),
        "title": l10n.format_value("managers-select-group-title"),
        "back_btn": l10n.format_value("back-btn"),
    }


async def on_group_selected(
    callback: CallbackQuery,
    widget: Any,
    manager: DialogManager,
    item_id: str,
):
    manager.dialog_data["group_id"] = int(item_id)
    await manager.switch_to(ManagersSG.select_admin)


async def get_admins(
    uow: UnitOfWork,
    dialog_manager: DialogManager,
    l10n: FluentLocalization,
    **kwargs,
):
    group = await uow.groups.get_by_id(dialog_manager.dialog_data["group_id"])
    bot = dialog_manager.middleware_data["bot"]

    try:
        admins = await bot.get_chat_administrators(group.telegram_id)
    except Exception as exc:
        logger.error("Unable to fetch group administrators: {}", exc)
        return {
            "admins": [],
            "title": l10n.format_value("managers-select-admin-title", {"group": group.title}),
            "back_btn": l10n.format_value("back-btn"),
            "error": l10n.format_value("admins-fetch-error"),
            "has_admins": False,
        }

    items = []
    for admin in admins:
        user = admin.user
        if user.is_bot or user.id == settings.superadmin_id:
            continue
        db_user = await uow.users.get_by_telegram_id(user.id)
        mark = "✅ " if db_user and db_user.id == group.manager_id else ""
        items.append(AdminView(user.id, f"{mark}{user.full_name}"))

    return {
        "admins": items,
        "title": l10n.format_value("managers-select-admin-title", {"group": group.title}),
        "back_btn": l10n.format_value("back-btn"),
        "error": "",
        "has_admins": bool(items),
    }


async def on_admin_selected(
    callback: CallbackQuery,
    widget: Any,
    manager: DialogManager,
    item_id: str,
):
    telegram_id = int(item_id)
    uow: UnitOfWork = manager.middleware_data["uow"]
    group_id = manager.dialog_data["group_id"]
    group = await uow.groups.get_by_id(group_id)
    member = await manager.middleware_data["bot"].get_chat_member(group.telegram_id, telegram_id)
    user = member.user

    db_user = await uow.users.get_by_telegram_id(telegram_id)
    if not db_user:
        db_user = DBUser(
            telegram_id=telegram_id,
            username=user.username,
            full_name=user.full_name,
            language_code=user.language_code if user.language_code in {"ru", "en"} else "en",
        )
        await uow.users.add(db_user)
        await uow.session.flush()

    await uow.groups.update(group_id, {"manager_id": db_user.id})
    await uow.commit()
    await callback.answer("Manager assigned")


async def back_to_admin(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.start(AdminSG.main, mode=StartMode.RESET_STACK)


managers_dialog = Dialog(
    Window(
        Format("{title}"),
        ScrollingGroup(
            Select(
                Format("{item.title}"),
                id="group_select",
                item_id_getter=lambda item: item.id,
                items="groups",
                on_click=on_group_selected,
            ),
            id="groups_scroll",
            width=1,
            height=5,
        ),
        Button(Format("{back_btn}"), id="back_admin", on_click=back_to_admin),
        state=ManagersSG.select_group,
        getter=get_groups,
    ),
    Window(
        Format("{title}"),
        Format("{error}", when="error"),
        ScrollingGroup(
            Select(
                Format("{item.name}"),
                id="admin_select",
                item_id_getter=lambda item: item.telegram_id,
                items="admins",
                on_click=on_admin_selected,
            ),
            id="admins_scroll",
            width=1,
            height=5,
            when="has_admins",
        ),
        Button(Format("{back_btn}"), id="back_groups", on_click=lambda c, b, m: m.switch_to(ManagersSG.select_group)),
        state=ManagersSG.select_admin,
        getter=get_admins,
    ),
)
