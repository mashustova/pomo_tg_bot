from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from utils.timezones import create_timezone_keyboard, validate_timezone
from data_manager import set_timezone

router = Router()


@router.message(Command("set_timezone"))
async def set_user_timezone(message: types.Message, state: FSMContext):
    keyboard = create_timezone_keyboard()
    await message.answer(
        "Пожалуйста, выбери свой часовой пояс из списка ниже или нажми 'Другой', чтобы ввести его вручную.",
        reply_markup=keyboard,
    )
    await state.set_state("waiting_for_timezone")


@router.callback_query()
async def handle_timezone_selection(
    callback_query: types.CallbackQuery, state: FSMContext
):
    timezone = callback_query.data
    # Если был выбран "Другой", запросим ввод вручную
    if timezone == "other":
        await callback_query.message.answer(
            "Пожалуйста, укажи свой часовой пояс (например, 'Europe/Moscow')."
        )
        await state.set_state("waiting_for_manual_timezone")
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
    await state.set_state("started_auth")
