import datetime
import json


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


def format_datetime(datetime_str):
    """
    Преобразует строку с датой и временем в более читаемый формат.
    """
    try:
        # Преобразуем строку ISO 8601 в объект datetime
        dt = datetime.datetime.fromisoformat(datetime_str)
        # Возвращаем в виде "ДД Месяц ГГГГ, ЧЧ:ММ"
        return dt.strftime("%d %B %Y года, %H:%M")
    except ValueError:
        return "Не указано"


async def generate_user_message_task(event_data):
    """
    Формирует сообщение для пользователя на основе данных события.
    """
    title = event_data.get("title", "Без названия")
    due = event_data.get("due", "Не указано")

    date_formatted = format_datetime(due) if due != "Не указано" else due

    if due == "Не указано":
        return f"Для задачи '{title}' необходимо уточнить дату и время выполнения."

    return (
        f"🔄 Задача: '{title}'\n"
        f"✅ Время выполнения: {date_formatted}.\n"
        f"💡 Для изменения данных воспользуйтесь соответствующими командами."
    )


async def handle_gpt_response_task(response, state, user_timezone):
    """
    Обрабатывает ответ GPT, обновляет словарь события и возвращает сообщение для пользователя.
    """
    try:
        # Парсим данные от GPT
        event_data_from_gpt = await parse_gpt_response_task(response)

        # Проверяем на прошедшее время
        start_datetime = datetime.datetime.fromisoformat(event_data_from_gpt["due"])
        if start_datetime < datetime.datetime.now():
            return f"Невозможно установить задачу на прошедшее время: {start_datetime}."

        # Сохраняем данные в состояние
        await state.update_data(event_data=event_data_from_gpt)

        # Генерируем сообщение для пользователя
        user_message = await generate_user_message_task(event_data_from_gpt)
        print("итоговый словарь", event_data_from_gpt)
        return user_message
    except ValueError as e:
        return f"Ошибка: {e}"
