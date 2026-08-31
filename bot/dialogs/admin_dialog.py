from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, StartMode, Window
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Format
from fluent.runtime import FluentLocalization

from bot.dialogs.states import AdminSG, AdsSG, GroupsSG, ManagersSG


async def get_admin_data(l10n: FluentLocalization, **kwargs):
    return {
        "title": l10n.format_value("admin-panel-title"),
        "groups_btn": l10n.format_value("admin-groups-btn"),
        "managers_btn": l10n.format_value("admin-managers-btn"),
        "ads_btn": l10n.format_value("admin-ads-btn"),
        "language_btn": l10n.format_value("admin-language-btn"),
    }


async def on_admin_groups_click(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.start(GroupsSG.main, mode=StartMode.RESET_STACK)


async def on_admin_managers_click(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.start(ManagersSG.select_group, mode=StartMode.RESET_STACK)


async def on_admin_ads_click(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.start(AdsSG.main, mode=StartMode.RESET_STACK)


async def on_admin_language_click(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(AdminSG.language)


async def get_language_data(l10n: FluentLocalization, **kwargs):
    return {
        "title": l10n.format_value("language-selection-title"),
        "ru_btn": l10n.format_value("language-ru-btn"),
        "en_btn": l10n.format_value("language-en-btn"),
        "back_btn": l10n.format_value("back-btn"),
    }


async def on_language_selected(callback: CallbackQuery, button: Button, manager: DialogManager):
    lang_code = button.widget_id.split("_")[1]
    state = manager.middleware_data["state"]
    await state.update_data(locale=lang_code)

    uow = manager.middleware_data.get("uow")
    if uow:
        user = await uow.users.get_by_telegram_id(callback.from_user.id)
        if user:
            await uow.users.update(user.id, {"language_code": lang_code})
            await uow.commit()

    await callback.answer("Language changed")
    await manager.switch_to(AdminSG.main)


admin_dialog = Dialog(
    Window(
        Format("{title}"),
        Button(Format("{groups_btn}"), id="admin_groups", on_click=on_admin_groups_click),
        Button(Format("{managers_btn}"), id="admin_managers", on_click=on_admin_managers_click),
        Button(Format("{ads_btn}"), id="admin_ads", on_click=on_admin_ads_click),
        Button(Format("{language_btn}"), id="admin_language", on_click=on_admin_language_click),
        state=AdminSG.main,
        getter=get_admin_data,
    ),
    Window(
        Format("{title}"),
        Button(Format("{ru_btn}"), id="lang_ru", on_click=on_language_selected),
        Button(Format("{en_btn}"), id="lang_en", on_click=on_language_selected),
        Button(Format("{back_btn}"), id="back", on_click=lambda c, b, m: m.switch_to(AdminSG.main)),
        state=AdminSG.language,
        getter=get_language_data,
    ),
)
