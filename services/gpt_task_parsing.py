import datetime
import json
from utils.datetime_utils import format_datetime


async def parse_gpt_response_task(response):
    """
    Парсит ответ GPT и возвращает словарь с обязательными полями для задачи.
    """
    try:
        parsed_data = json.loads(response)  # GPT должен возвращать JSON
        required_keys = ["title", "due"]

        # Проверка на наличие обязательных ключей
        for key in required_keys:
            if key not in parsed_data or not parsed_data[key]:
                raise ValueError(f"Отсутствует обязательное поле: {key}")

        return parsed_data
    except json.JSONDecodeError as e:
        raise ValueError(f"Ошибка парсинга JSON: {e}")
    except Exception as e:
        raise ValueError(f"Ошибка обработки ответа GPT: {e}")


async def generate_user_message_task(task_data):
    """
    Формирует сообщение для пользователя на основе данных задачи.
    """
    title = task_data.get("title", "Без названия")
    due = task_data.get("due", "Не указано")

    due_formatted = format_datetime(due) if due != "Не указано" else due

    if due == "Не указано":
        return f"Для задачи '{title}' необходимо уточнить дату и время выполнения."

    return (
        f"🔄 Задача: '{title}'\n"
        f"✅ Время выполнения: {due_formatted}.\n"
        f"💡 Для изменения данных воспользуйтесь соответствующими командами."
    )
