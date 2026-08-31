from typing import Any

from aiogram.exceptions import TelegramNotFound
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, StartMode, Window
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import Button, ScrollingGroup, Select
from aiogram_dialog.widgets.text import Format
from fluent.runtime import FluentLocalization

from bot.dialogs.states import AdminSG, GroupsSG
from database.db import UnitOfWork
from database.models import Group
from logger import logger


async def get_groups(uow: UnitOfWork, l10n: FluentLocalization, **kwargs):
    groups = await uow.groups.get_all()
    return {
        "groups": groups,
        "title": l10n.format_value("groups-management-title"),
        "add_group_btn": l10n.format_value("add-group-btn"),
        "back_btn": l10n.format_value("back-btn"),
    }


async def get_group_details(
    uow: UnitOfWork,
    dialog_manager: DialogManager,
    l10n: FluentLocalization,
    **kwargs,
):
    group_id = dialog_manager.dialog_data.get("selected_group_id")
    group = await uow.groups.get_by_id(group_id) if group_id else None
    if not group:
        return {}

    manager_info = l10n.format_value("no-manager")
    if group.manager_id:
        manager = await uow.users.get_by_id(group.manager_id)
        if manager:
            manager_info = f"@{manager.username}" if manager.username else manager.full_name

    return {
        "title": l10n.format_value("group-details-title"),
        "group_title": group.title,
        "group_id": group.telegram_id,
        "group_description": group.description or l10n.format_value("no-description"),
        "group_invite_link": group.invite_link or l10n.format_value("no-invite-link"),
        "group_manager": manager_info,
        "back_btn": l10n.format_value("back-btn"),
    }


async def on_group_selected(
    callback: CallbackQuery,
    widget: Any,
    dialog_manager: DialogManager,
    item_id: str,
):
    group = await dialog_manager.middleware_data["uow"].groups.get_by_telegram_id(int(item_id))
    if group:
        dialog_manager.dialog_data["selected_group_id"] = group.id
        await dialog_manager.switch_to(GroupsSG.group_details)


async def on_group_delete(callback: CallbackQuery, button: Button, manager: DialogManager):
    group_id = manager.dialog_data.get("selected_group_id")
    if group_id:
        uow: UnitOfWork = manager.middleware_data["uow"]
        await uow.groups.delete(group_id)
        await uow.commit()
    await manager.start(GroupsSG.main, mode=StartMode.RESET_STACK)


def parse_group_input(value: str) -> str | None:
    value = value.strip()
    if value.startswith("https://t.me/"):
        value = value.rsplit("/", 1)[-1]
        if value.startswith("+"):
            return None
        return f"@{value}"
    if value.startswith("@") or value.startswith("-") or value.isdigit():
        return value
    return f"@{value}" if value else None


async def on_add_group_input(
    message: Message,
    widget: TextInput,
    dialog_manager: DialogManager,
    *args,
    **kwargs,
):
    l10n: FluentLocalization = dialog_manager.middleware_data["l10n"]
    uow: UnitOfWork = dialog_manager.middleware_data["uow"]
    parsed_input = parse_group_input(message.text or "")

    if not parsed_input:
        await message.answer(l10n.format_value("group-input-error"))
        return

    bot = dialog_manager.middleware_data.get("bot")
    if not bot:
        await message.answer(l10n.format_value("bot-instance-error"))
        return

    try:
        chat = await bot.get_chat(parsed_input)
    except TelegramNotFound:
        await message.answer(l10n.format_value("group-not-found-error"))
        return
    except Exception as exc:
        logger.error("Unable to fetch group: {}", exc)
        await message.answer(l10n.format_value("group-fetch-error", {"error": str(exc)}))
        return

    if await uow.groups.get_by_telegram_id(chat.id):
        await message.answer(l10n.format_value("group-exists-error"))
        return

    invite_link = chat.invite_link
    if not invite_link and chat.username:
        invite_link = f"https://t.me/{chat.username}"

    group = Group(
        telegram_id=chat.id,
        title=chat.title or str(chat.id),
        description=chat.description,
        photo_id=chat.photo.big_file_id if chat.photo else None,
        invite_link=invite_link,
    )
    await uow.groups.add(group)
    await uow.commit()
    await dialog_manager.switch_to(GroupsSG.main)


async def back_to_admin(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.start(AdminSG.main, mode=StartMode.RESET_STACK)


groups_dialog = Dialog(
    Window(
        Format("{title}"),
        ScrollingGroup(
            Select(
                Format("{item.title}"),
                id="group_select",
                item_id_getter=lambda item: item.telegram_id,
                items="groups",
                on_click=on_group_selected,
            ),
            id="groups_scroll",
            width=1,
            height=5,
        ),
        Button(Format("{add_group_btn}"), id="add_group", on_click=lambda c, b, m: m.switch_to(GroupsSG.add_group)),
        Button(Format("{back_btn}"), id="back_admin", on_click=back_to_admin),
        state=GroupsSG.main,
        getter=get_groups,
    ),
    Window(
        Format("{enter_group_link}"),
        TextInput(id="new_group_input", on_success=on_add_group_input),
        Button(Format("{cancel_btn}"), id="cancel", on_click=lambda c, b, m: m.switch_to(GroupsSG.main)),
        state=GroupsSG.add_group,
        getter=lambda l10n, **kwargs: {
            "enter_group_link": l10n.format_value("enter-group-link"),
            "cancel_btn": l10n.format_value("cancel-btn"),
        },
    ),
    Window(
        Format("{title}\n"),
        Format("Title: {group_title}"),
        Format("Telegram ID: {group_id}"),
        Format("Invite link: {group_invite_link}"),
        Format("Description: {group_description}"),
        Format("Manager: {group_manager}"),
        Button(Format("🗑 Delete Group"), id="delete_group", on_click=on_group_delete),
        Button(Format("{back_btn}"), id="back_groups", on_click=lambda c, b, m: m.switch_to(GroupsSG.main)),
        state=GroupsSG.group_details,
        getter=get_group_details,
    ),
)
