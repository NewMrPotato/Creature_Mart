# aiogram
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

# Кнопки для главного меню
profile_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Меню🌐")]],
    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder="Choice a button",
    selective=True,
)
