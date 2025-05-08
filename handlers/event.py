from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from services.google_calendar import GoogleCalendar
from utils.gpt import get_gpt_response_event
from data_manager import get_timezone

router = Router()


@router.message(Command("add_event"))
async def start_event_adding(message: types.Message, state: FSMContext):
    await state.set_state("waiting_for_event_description")
    await message.answer(
        "Хорошо! Отправь описание события, включая дату, время и участников."
    )


@router.message(lambda message: state.get_state() == "waiting_for_event_description")
async def event_adding(message: types.Message, state: FSMContext):
    user_input = message.text
    user_timezone = get_timezone(message.from_user.id)
    if not user_timezone:
        await message.answer(
            "Ваш часовой пояс не установлен. Установите его с помощью команды /set_timezone."
        )
        return
    # Генерируем JSON для события через GPT
    event_data = await get_gpt_response_event(user_input, user_timezone)
    if (
        not event_data.get("summary")
        or not event_data.get("start")
        or not event_data.get("end")
    ):
        await message.answer(
            "Некоторые данные события отсутствуют. Пожалуйста, уточните."
        )
        return
    # Добавляем событие через Google Calendar API
    calendar_service = GoogleCalendar()
    calendar_service.authenticate_user()
    calendar_service.add_event(event_data)
    await message.answer(f"Событие '{event_data['summary']}' успешно добавлено!")
    await state.clear()
