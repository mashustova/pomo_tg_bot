import pytz
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Определяем список часовых поясов
timezones = {
    "Калининград": "Europe/Kaliningrad",  # UTC+2
    "Москва": "Europe/Moscow",  # UTC+3
    "Самара": "Europe/Samara",  # UTC+4
    "Екатеринбург": "Asia/Yekaterinburg",  # UTC+5
    "Омск": "Asia/Omsk",  # UTC+6
    "Красноярск": "Asia/Krasnoyarsk",  # UTC+7
    "Иркутск": "Asia/Irkutsk",  # UTC+8
    "Якутск": "Asia/Yakutsk",  # UTC+9
    "Владивосток": "Asia/Vladivostok",  # UTC+10
    "Магадан": "Asia/Magadan",  # UTC+11
    "Камчатка": "Asia/Kamchatka",  # UTC+12
}


def create_timezone_keyboard():
    """Создает клавиатуру для выбора часового пояса."""
    keyboard = []
    # Создаем кнопки с городами, где callback_data будет содержать часовой пояс
    for city, timezone in timezones.items():
        keyboard.append([InlineKeyboardButton(text=city, callback_data=timezone)])
    keyboard.append([InlineKeyboardButton(text="Другой", callback_data="other")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def validate_timezone(timezone: str) -> bool:
    """Проверяет корректность часового пояса."""
    return timezone in pytz.all_timezones
