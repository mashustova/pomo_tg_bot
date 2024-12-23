import asyncio
import datetime
import json
import os
import time


import pytz
import schedule
from aiogram import Bot, Dispatcher, F, Router, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from pomo_token import TOKEN
from user_states import Form
from data_manager import get_timezone, set_timezone
from event_manager import reset_event_data, update_event_field, get_event_data
from timezone_manager import create_timezone_keyboard, validate_timezone
from gpt_adding_event import handle_gpt_response
from gpt_adding_task import handle_gpt_response_task
from gpt_integration import get_gpt_response


bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

command_router = Router()
dp.include_router(command_router)


class GoogleTasks:
    SCOPES = ["https://www.googleapis.com/auth/tasks"]
    FILE_PATH = "todo-bot-calendar-db2a7174b28f.json"

    def __init__(self):
        self.service = None

    def authenticate_user(self):
        """
        Аутентифицирует пользователя через OAuth 2.0 и инициализирует Google Tasks API сервис.
        """
        creds = None

        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file(
                "token.json", ["https://www.googleapis.com/auth/tasks"]
            )
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "secretfile.json", ["https://www.googleapis.com/auth/tasks"]
                )
                creds = flow.run_local_server(port=0)
            print("got here")
            with open("token.json", "w") as token:
                token.write(creds.to_json())

        self.service = build("tasks", "v1", credentials=creds)

    def add_task(self, info):
        """
        Добавляет задачу в список задач.
        """

        if not self.service:
            print("Сначала выполните авторизацию.")
            return None

        task = {
            "title": info["title"],
            "due": info["due"],
        }

        try:
            result = (
                self.service.tasks().insert(tasklist="@default", body=task).execute()
            )

            print(f"Задача добавлена: {result.get('title')}, ID: {result.get('id')}")
            return result

        except HttpError as error:
            print(f"Произошла ошибка: {error}")
            return None


class GoogleCalendar:
    SCOPES = ["https://www.googleapis.com/auth/calendar"]
    FILE_PATH = "todo-bot-calendar-db2a7174b28f.json"

    def __init__(self):
        self.service = None

    def authenticate_user(self):
        """
        Аутентифицирует пользователя через OAuth 2.0 и инициализирует Google Tasks API сервис.
        """
        creds = None
        if os.path.exists("token_calendar.json"):
            creds = Credentials.from_authorized_user_file(
                "token_calendar.json", ["https://www.googleapis.com/auth/calendar"]
            )
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "secretfile.json", ["https://www.googleapis.com/auth/calendar"]
                )
                creds = flow.run_local_server(port=0)
            with open("token_calendar.json", "w") as token:
                token.write(creds.to_json())

        self.service = build("calendar", "v3", credentials=creds)

    def add_event(self, info):
        """
        Добавляет событие в календаря по его названию и дате.
        """
        event = {
            "summary": info["summary"],
            "start": {
                "dateTime": info["start"]["dateTime"],
                "timeZone": info["start"]["timeZone"],
            },
            "end": {
                "dateTime": info["end"]["dateTime"],
                "timeZone": info["end"]["timeZone"],
            },
        }

        try:
            return (
                self.service.events()
                .insert(calendarId=info["calendar_id"], body=event)
                .execute()
            )
        except HttpError as error:
            print(f"An error occurred: {error}")
            return None


# Обработчик команды /start
@command_router.message(CommandStart())
async def cmd_hello(message: Message, state: FSMContext):
    # Приветственное сообщение
    await state.clear()
    await message.answer(
        f"Привет, {(message.from_user.full_name)}!\nЯ готов помочь тебе с добавлением задач и дел в Google Calendar!\n"
    )
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="/set_timezone")]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await message.answer(
        "Чтобы установить часовой пояс, воспользуйся командой /set_timezone или нажми на кнопку ниже:",
        reply_markup=keyboard,
    )


# Обработчик команды /help
@command_router.message(Command("help"))
async def commands_list(message: types.Message):
    commands_message = "\n".join(
        [f"{command}: {description}" for command, description in commands.items()]
    )
    await bot.send_message(message.from_user.id, "Список команд:\n" + commands_message)


# Отменить текущее действие и завершить состояние
@command_router.message(
    Command("cancel")
    or StateFilter(Form.started_auth)
    or StateFilter(Form.waiting_for_auth)
    or StateFilter(Form.waiting_for_timezone)
)
async def cancel_handler(message: Message, state: FSMContext):
    # Завершение состояния
    await state.clear()
    await message.answer(
        "Операция отменена. Чтобы увидеть список команд, используй /help."
    )


# Обработчик команды для запроса часового пояса
@command_router.message(Command("set_timezone"))
async def set_user_timezone(message: types.Message, state: FSMContext):
    keyboard = create_timezone_keyboard()
    await message.answer(
        "Пожалуйста, выбери свой часовой пояс из списка ниже или нажми 'Другой', чтобы ввести его вручную.",
        reply_markup=keyboard,
    )
    await state.set_state(Form.waiting_for_timezone)


# Обработка часового пояса пользователя
@command_router.callback_query(StateFilter(Form.waiting_for_timezone))
async def handle_timezone_selection(
    callback_query: types.CallbackQuery, state: FSMContext
):
    timezone = callback_query.data
    # Если был выбран "Другой", запросим ввод вручную
    if timezone == "other":
        await callback_query.message.answer(
            "Пожалуйста, укажи свой часовой пояс (например, 'Europe/Moscow')."
        )
        await state.set_state(Form.waiting_for_manual_timezone)
        return
    # Проверка на корректность введенного часового пояса
    if not validate_timezone(timezone):
        await callback_query.message.answer(
            "Некорректный часовой пояс. Пожалуйста, попробуй снова."
        )
        return
    # Сохраняем часовой пояс
    set_timezone(callback_query.from_user.id, timezone)

    await callback_query.message.answer(f"Часовой пояс '{timezone}' успешно сохранен!")
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="/auth")]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await callback_query.message.answer(
        "Для авторизации в Google Calendar, нажми на кнопку ниже:",
        reply_markup=keyboard,
    )
    await state.set_state(Form.started_auth)


@command_router.message(Command("auth") or StateFilter(Form.started_auth))
async def get_gmail(message: Message, state: FSMContext):
    await message.answer(
        "Для авторизации отправь мне почту, привязанную к Google Calendar, в формате pomo@gmail.com",
    )
    await state.set_state(Form.waiting_gmail)


@command_router.message(StateFilter(Form.waiting_gmail))
async def handle_register_choice(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    user_gmail = message.text.strip()
    if "@" not in user_gmail or not user_gmail.endswith(".com"):
        await message.answer("Пожалуйста, отправьте корректный Gmail-адрес.")
        return
    # сохранить gmail в json файл по id пользователя
    try:
        with open("user_gmails.json", "r") as file:
            gmails_data = json.load(file) if file.read().strip() else {}
    except json.JSONDecodeError:
        gmails_data = {}
        gmails_data[user_id] = user_gmail

    # Сохраняем обновленный файл
    with open("user_gmails.json", "w") as file:
        json.dump(gmails_data, file, indent=4)

    await message.answer(
        "Ты успешно авторизовался, можем приступать к добавлению задач в Google Calendar!"
    )
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Хочу добавить событие!")],
            [KeyboardButton(text="Хочу добавить задачу!")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await message.answer(
        "Если хочешь добавить новое событие или дело, \nнажми на кнопку ниже или воспользуйся командами /add_event и /add_task.",
        reply_markup=keyboard,
    )
    await state.clear()


# Добавление задачи
@command_router.message(Command("add_task"))
@command_router.message(F.text.lower().contains("добавить задачу"))
async def start_task_adding(message: Message, state: FSMContext):
    # Переходим в состояние ожидания описания события
    await state.set_state(Form.waiting_for_task_description)
    print(f"State set to: {await state.get_state()}")  # Debugging

    # Просим пользователя отправить описание события
    await message.answer(
        "Отлично! Тогда отправь мне задачу и время, на которое ее нужно установить."
    )


@command_router.message(StateFilter(Form.waiting_for_task_description))
async def task_adding(message: Message, state: FSMContext):
    user_input = message.text
    user_timezone = get_timezone(message.from_user.id)
    print(f"Часовой пояс пользователя: {user_timezone}")
    if not user_timezone:
        await message.answer(
            "Ваш часовой пояс не установлен. Установите его с помощью команды /set_timezone."
        )
        return
    existing_data = await state.get_data()
    prompt = (
        f"На основе текста пользователя сформируй JSON для задачи. Текст: '{user_input}'.\n"
        f"Из предыдущих ответов известно {existing_data}. Обязательные поля:"
        f"- title: краткое описание задачи(не пиши слово название и символы кроме букв и цифр, используй пробелы).\n"
        f"- due: дата и время начала в формате ISO 8601, например '2024-12-19T15:30:00'.\n"
        f"Пример ответа:\n"
        f'{{\n  "title": "Отправить письмо",\n  "due": "2024-12-19T15:00:00"\n}}\n'
        f"Если текст содержит ключевые фразы 'сегодня', 'завтра', дни недели, преобразуй их в дату."
        f"Сегодня: {datetime.date.today()}, {datetime.date.today().strftime('%A')} "
        f"Если пользователь не указал дату, время, место или описание, оставь соответствующие поля пустыми. Не добавляй их самостоятельно. Только анализируй текст пользователя, не делай предположений о недостающих данных."
    )
    # Отправляем запрос к GPT
    gpt_response = await get_gpt_response(prompt)
    print(f"GPT response: {gpt_response}")  # Debugging

    task_data = json.loads(gpt_response)
    missing_fields = []
    if not task_data.get("title"):
        missing_fields.append("краткое описание задачи")
    if not task_data.get("due"):
        missing_fields.append("время выполнения")

    # Если данные неполные, запрашиваем уточнения у пользователя
    if missing_fields:
        await state.update_data(task_data=task_data)  # Сохраняем частичные данные
        await message.answer(
            f"Некоторые данные отсутствуют: {', '.join(missing_fields)}. Пожалуйста, уточните."
        )
        return
    due_date = task_data.get("due") + ".000Z"
    task_data["due"] = due_date
    # Создаём объект класса GoogleTasks
    tasks_obj = GoogleTasks()

    # Авторизуемся
    tasks_obj.authenticate_user()

    # Добавляем задачу
    task_info = task_data
    tasks_obj.add_task(task_info)

    user_message = await handle_gpt_response_task(gpt_response, state, user_timezone)
    await message.answer(user_message)
    await state.clear()


# Добавление события
@command_router.message(Command("add_event"))
@command_router.message(F.text.lower().contains("добавить событие"))
async def event_adding(message: Message, state: FSMContext):
    # Переходим в состояние ожидания описания события
    await state.set_state(Form.waiting_for_event_description)
    print(f"State set to: {await state.get_state()}")  # Debugging

    # Просим пользователя отправить описание события
    await message.answer(
        "Отлично! Тогда отправь мне описание события, время его начала и конца."
    )


@command_router.message(StateFilter(Form.waiting_for_event_description))
async def title_adding(message: Message, state: FSMContext):
    user_input = message.text
    user_timezone = get_timezone(message.from_user.id)
    if not user_timezone:
        await message.answer(
            "Ваш часовой пояс не установлен. Установите его с помощью команды /set_timezone."
        )
        return
    print("we are here")
    existing_data = await state.get_data()
    prompt = (
        f"На основе текста пользователя сформируй JSON для события. Текст: '{user_input}'.\n"
        f"Из предыдущих ответов известно {existing_data}.Обязательные поля:"
        f"- summary: краткое описание события(не пиши слово название и символы кроме букв и цифр, используй пробелы).\n"
        f"- start: объект с ключом dateTime (дата и время начала в формате ISO 8601, например '2024-12-19T15:30:00').\n"
        f"- end: объект с ключом dateTime (дата и время окончания в формате ISO 8601).\n\n"
        f"Пример ответа:\n"
        f'{{\n  "summary": "Встреча с командой",\n  "start": {{"dateTime": "2024-12-19T15:00:00"}},\n'
        f'  "end": {{"dateTime": "2024-12-19T16:00:00"}},\n  "location": "Офис",\n'
        f'  "description": "Обсуждение проекта"\n}}\n\n'
        f"Если текст содержит ключевые фразы 'сегодня', 'завтра', дни недели, преобразуй их в дату."
        f"Сегодня: {datetime.date.today()}, {datetime.date.today().strftime('%A')} "
        f"Если пользователь не указал дату, время, место или описание, оставь соответствующие поля пустыми. Не добавляй их самостоятельно. Только анализируй текст пользователя, не делай предположений о недостающих данных."
    )
    # Отправляем запрос к GPT
    gpt_response = await get_gpt_response(prompt)
    print(f"GPT response: {gpt_response}")  # Debugging

    event_data = json.loads(gpt_response)
    missing_fields = []
    if not event_data.get("summary"):
        missing_fields.append("краткое описание события")
    if not event_data.get("start", {}).get("dateTime"):
        missing_fields.append("время начала события")
    if not event_data.get("end", {}).get("dateTime"):
        missing_fields.append("время окончания события")

    # Если данные неполные, запрашиваем уточнения у пользователя
    if missing_fields:
        await state.update_data(event_data=event_data)  # Сохраняем частичные данные
        await message.answer(
            f"Некоторые данные отсутствуют: {', '.join(missing_fields)}. Пожалуйста, уточните."
        )
        return

    # Добавляем часовой пояс пользователя в start и end
    event_data["start"]["timeZone"] = user_timezone
    event_data["end"]["timeZone"] = user_timezone
    user_id = str(message.from_user.id)
    with open("user_gmails.json", "r") as file:
        data = json.load(file)
        if user_id in data:
            calendar_id = data[user_id]
            event_data["calendar_id"] = calendar_id
    obj = GoogleCalendar()

    # Авторизуемся
    obj.authenticate_user()
    # Добавляем задачу
    obj.add_event(info=event_data)

    # Обрабатываем ответ GPT
    user_message = await handle_gpt_response(gpt_response, state, user_timezone)
    await message.answer(user_message)
    await state.clear()


@command_router.message(Command("reset_event"))
async def reset_event(message: Message):
    reset_event_data()
    await message.answer("Данные события сброшены.")


commands = {
    "/start": "Запуск бота",
    "/help": "Просмотр доступных команд",
    "/cancel": "Вернуться назад",
    "/auth": "Авторизоваться в Google Calendar",
    "/set_timezone": "Установить часовой пояс",
    "/add_task": "Добавить новое задание",
    "/add_event": "Добавить новое событие",
    "/reset_event": "Сбросить текущее событие",
}


# Обработчик неожиданных сообщений
@command_router.message(F.text)
async def handle_random_message(message: Message):
    await message.answer("i'm just a bot 🥺✨💞")
    await message.answer(
        "Я не понял, что это значит, используй /help чтобы увидеть доступные команды."
    )


# Обработчик изображений и других типов контента
@command_router.message(~F.text)
async def handle_photo(message: Message):
    await message.answer("К сожалению, пока я понимаю только текст...\U0001F622")


if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
