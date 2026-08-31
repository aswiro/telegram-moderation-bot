from aiogram.enums import ContentType
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, StartMode, Window
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Row
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Format
from fluent.runtime import FluentLocalization

from bot.dialogs.states import AdminSG, AdsSG
from database.db import UnitOfWork
from database.models import Ad


async def get_ad_view(
    uow: UnitOfWork,
    dialog_manager: DialogManager,
    l10n: FluentLocalization,
    **kwargs,
):
    ads = await uow.ads.get_all()
    if not ads:
        return {
            "ad_text": "",
            "ad_media": None,
            "has_ads": False,
            "has_next": False,
            "has_prev": False,
            "index_info": "0/0",
            "title": l10n.format_value("ads-management-title"),
            "add_btn": l10n.format_value("ads-add-btn"),
            "back_btn": l10n.format_value("back-btn"),
        }

    index = max(0, min(dialog_manager.dialog_data.get("current_index", 0), len(ads) - 1))
    dialog_manager.dialog_data["current_index"] = index
    ad = ads[index]

    media = None
    if ad.content_type == "photo" and ad.file_id:
        media = MediaAttachment(ContentType.PHOTO, file_id=MediaId(ad.file_id))
    elif ad.content_type == "video" and ad.file_id:
        media = MediaAttachment(ContentType.VIDEO, file_id=MediaId(ad.file_id))

    return {
        "ad_text": ad.text or "",
        "ad_media": media,
        "has_ads": True,
        "has_next": index < len(ads) - 1,
        "has_prev": index > 0,
        "index_info": f"{index + 1}/{len(ads)}",
        "title": l10n.format_value("ads-management-title"),
        "add_btn": l10n.format_value("ads-add-btn"),
        "back_btn": l10n.format_value("back-btn"),
    }


async def on_prev(callback: CallbackQuery, button: Button, manager: DialogManager):
    manager.dialog_data["current_index"] = max(0, manager.dialog_data.get("current_index", 0) - 1)
    await manager.switch_to(AdsSG.main)


async def on_next(callback: CallbackQuery, button: Button, manager: DialogManager):
    manager.dialog_data["current_index"] = manager.dialog_data.get("current_index", 0) + 1
    await manager.switch_to(AdsSG.main)


async def on_delete(callback: CallbackQuery, button: Button, manager: DialogManager):
    uow: UnitOfWork = manager.middleware_data["uow"]
    ads = await uow.ads.get_all()
    index = manager.dialog_data.get("current_index", 0)
    if ads and 0 <= index < len(ads):
        await uow.ads.delete(ads[index].id)
        await uow.commit()
        manager.dialog_data["current_index"] = max(0, index - 1)
    await manager.switch_to(AdsSG.main)


async def on_announcement_message(
    message: Message,
    widget: MessageInput,
    dialog_manager: DialogManager,
):
    uow: UnitOfWork = dialog_manager.middleware_data["uow"]
    l10n: FluentLocalization = dialog_manager.middleware_data["l10n"]

    content_type = None
    file_id = None
    text = message.caption or message.text or ""

    if message.photo:
        content_type = "photo"
        file_id = message.photo[-1].file_id
    elif message.video:
        content_type = "video"
        file_id = message.video.file_id
    elif message.text:
        content_type = "text"

    if not content_type:
        await message.answer(l10n.format_value("ads-unsupported-type"))
        return

    await uow.ads.add(Ad(content_type=content_type, file_id=file_id, text=text))
    await uow.commit()
    await message.answer(l10n.format_value("ads-added-success"))


async def back_to_admin(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.start(AdminSG.main, mode=StartMode.RESET_STACK)


ads_dialog = Dialog(
    Window(
        Format("{title}"),
        DynamicMedia("ad_media", when="ad_media"),
        Format("{ad_text}"),
        Row(
            Button(Const("⬅️"), id="prev", on_click=on_prev, when="has_prev"),
            Button(Format("{index_info}"), id="page", when="has_ads"),
            Button(Const("➡️"), id="next", on_click=on_next, when="has_next"),
        ),
        Button(Const("🗑 Delete"), id="delete", on_click=on_delete, when="has_ads"),
        Button(Format("{add_btn}"), id="add", on_click=lambda c, b, m: m.switch_to(AdsSG.add_ad)),
        Button(Format("{back_btn}"), id="back", on_click=back_to_admin),
        state=AdsSG.main,
        getter=get_ad_view,
    ),
    Window(
        Const("Send text, a photo, or a video. You can add several items before returning."),
        MessageInput(
            on_announcement_message,
            content_types=[ContentType.PHOTO, ContentType.VIDEO, ContentType.TEXT],
        ),
        Button(Const("✅ Done"), id="done", on_click=lambda c, b, m: m.switch_to(AdsSG.main)),
        state=AdsSG.add_ad,
    ),
)
