from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

router = Router()


@router.message(CommandStart())
async def cmd_hello(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f"Привет, {message.from_user.full_name}!\n"
        "Я готов помочь тебе с добавлением задач и дел в Google Calendar!\n"
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
