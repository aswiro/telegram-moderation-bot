from aiogram.enums import ContentType
from aiogram.fsm.state import State, StatesGroup
from aiogram_dialog import Dialog, Window
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from aiogram_dialog.widgets.kbd import Url
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Format
from fluent.runtime import FluentLocalization

from database.db import UnitOfWork
from database.models import Group


class UserSG(StatesGroup):
    main = State()


async def get_random_group(uow: UnitOfWork, l10n: FluentLocalization, **kwargs):
    group: Group | None = await uow.groups.get_random()
    if not group:
        return {
            "group_title": l10n.format_value("no-groups-available"),
            "group_description": "",
            "group_photo": None,
            "invite_link": None,
            "join_btn": "",
        }

    group_photo = None
    if group.photo_id:
        group_photo = MediaAttachment(ContentType.PHOTO, file_id=MediaId(group.photo_id))

    return {
        "group_title": group.title,
        "group_description": group.description or "",
        "group_photo": group_photo,
        "invite_link": group.invite_link,
        "join_btn": l10n.format_value("join-group-btn"),
    }


user_dialog = Dialog(
    Window(
        DynamicMedia("group_photo", when="group_photo"),
        Format("{group_title}"),
        Format("{group_description}"),
        Url(Format("{join_btn}"), url=Format("{invite_link}"), when="invite_link"),
        state=UserSG.main,
        getter=get_random_group,
    )
)
