from aiogram.fsm.state import State, StatesGroup


class AdminSG(StatesGroup):
    main = State()
    language = State()


class GroupsSG(StatesGroup):
    main = State()
    add_group = State()
    group_details = State()


class ManagersSG(StatesGroup):
    select_group = State()
    select_admin = State()


class AdsSG(StatesGroup):
    main = State()
    add_ad = State()
