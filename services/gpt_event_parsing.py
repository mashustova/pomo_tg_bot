import datetime
import json
from utils.datetime_utils import format_datetime


async def parse_gpt_response_event(response):
    """
    Парсит ответ GPT и возвращает словарь с обязательными полями для события.
    """
    try:
        parsed_data = json.loads(response)  # GPT должен возвращать JSON
        required_keys = ["summary", "start", "end"]

        # Проверка на наличие обязательных ключей
        for key in required_keys:
            if key not in parsed_data or not parsed_data[key]:
                raise ValueError(f"Отсутствует обязательное поле: {key}")

        return parsed_data
    except json.JSONDecodeError as e:
        raise ValueError(f"Ошибка парсинга JSON: {e}")
    except Exception as e:
        raise ValueError(f"Ошибка обработки ответа GPT: {e}")


async def generate_user_message_event(event_data):
    """
    Формирует сообщение для пользователя на основе данных события.
    """
    summary = event_data.get("summary", "Без названия")
    start = event_data.get("start", {}).get("dateTime", "Не указано")
    end = event_data.get("end", {}).get("dateTime", "Не указано")

    start_formatted = format_datetime(start) if start != "Не указано" else start
    end_formatted = format_datetime(end) if end != "Не указано" else end

    if start == "Не указано" or end == "Не указано":
        return f"Для события '{summary}' необходимо уточнить дату и время."

    return (
        f"🎉 Событие: '{summary}'\n"
        f"📅 Дата и время: с {start_formatted} до {end_formatted}.\n\n"
        f"💡 Для изменения данных воспользуйтесь соответствующими командами."
    )
