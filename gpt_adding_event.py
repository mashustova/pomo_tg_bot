import datetime
import json


async def parse_gpt_response(response):
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


async def generate_user_message(event_data):
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


async def handle_gpt_response(response, state, user_timezone):
    """
    Обрабатывает ответ GPT, обновляет словарь события и возвращает сообщение для пользователя.
    """
    try:
        # Парсим данные от GPT
        event_data_from_gpt = await parse_gpt_response(response)

        # Добавляем часовой пояс пользователя
        event_data_from_gpt["start"]["timeZone"] = user_timezone
        event_data_from_gpt["end"]["timeZone"] = user_timezone

        # Проверяем на прошедшее время
        start_datetime = datetime.datetime.fromisoformat(
            event_data_from_gpt["start"]["dateTime"]
        )
        if start_datetime < datetime.datetime.now():
            return f"Невозможно установить событие на прошедшее время: {format_datetime(str(start_datetime))}."

        # Сохраняем данные в состояние
        await state.update_data(event_data=event_data_from_gpt)

        # Генерируем сообщение для пользователя
        user_message = await generate_user_message(event_data_from_gpt)
        print("итоговый словарь", event_data_from_gpt)
        return user_message
    except ValueError as e:
        return f"Ошибка: {e}"
