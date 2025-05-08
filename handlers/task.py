from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from services.google_tasks import GoogleTasks
from utils.gpt import get_gpt_response_task
from data_manager import get_timezone

router = Router()


@router.message(Command("add_task"))
async def start_task_adding(message: types.Message, state: FSMContext):
    await state.set_state("waiting_for_task_description")
    await message.answer(
        "Отлично! Отправь описание задачи и время, на которое её нужно установить."
    )


@router.message(lambda message: state.get_state() == "waiting_for_task_description")
async def task_adding(message: types.Message, state: FSMContext):
    user_input = message.text
    user_timezone = get_timezone(message.from_user.id)
    if not user_timezone:
        await message.answer(
            "Ваш часовой пояс не установлен. Установите его с помощью команды /set_timezone."
        )
        return
    # Генерируем JSON для задачи через GPT
    task_data = await get_gpt_response_task(user_input, user_timezone)
    if not task_data.get("title") or not task_data.get("due"):
        await message.answer(
            "Некоторые данные задачи отсутствуют. Пожалуйста, уточните."
        )
        return
    # Добавляем задачу через Google Tasks API
    tasks_service = GoogleTasks()
    tasks_service.authenticate_user()
    tasks_service.add_task(task_data)
    await message.answer(f"Задача '{task_data['title']}' успешно добавлена!")
    await state.clear()
