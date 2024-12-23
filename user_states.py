from aiogram.fsm.state import StatesGroup, State


class Form(StatesGroup):
    waiting_for_event_description = State()
    waiting_for_task_title = State()
    waiting_for_event_time = State()
    waiting_for_event_date = State()
    waiting_gmail = State()
    waiting_for_auth = State()
    waiting_for_task_description = State()
    started_auth = State()
    waiting_for_timezone = State()
    waiting_for_manual_timezone = State()
