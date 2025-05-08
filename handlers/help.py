from aiogram import Router, types
from aiogram.filters import Command

router = Router()

commands = {
    "/start": "Запуск бота",
    "/help": "Просмотр доступных команд",
    "/cancel": "Отмена текущего действия",
    "/auth": "Авторизация в Google Calendar",
    "/set_timezone": "Установить часовой пояс",
    "/add_task": "Добавить новую задачу",
    "/add_event": "Добавить новое событие",
    "/reset_event": "Сбросить данные текущего события",
}


@router.message(Command("help"))
async def commands_list(message: types.Message):
    commands_message = "\n".join(
        [f"{command}: {description}" for command, description in commands.items()]
    )
    await message.answer(f"Список команд:\n{commands_message}")
