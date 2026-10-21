import asyncio
from html import escape

from aiogram import F, types

from database import OperationError
from handlers.users.navigation import show_screen
from keyboards.inline.inline_buttons import back_to_profile_inline_keyboard, profile_inline_keyboard
from loader import db, router


async def show_profile_text_request(message: types.Message | types.CallbackQuery, notice=""):
    await show_screen(
        message,
        (f"{escape(notice)}\n\n" if notice else "")
        + "🌐<b>Меню</b>\n\n<i>Выберите следующее действие:</i>",
        reply_markup=profile_inline_keyboard,
    )


async def show_profile_callback_request(callback: types.CallbackQuery, notice=""):
    await show_profile_text_request(callback, notice)


@router.message(F.text == "Меню🌐")
async def menu_demonstration(message: types.Message):
    await asyncio.to_thread(db.cancel, message.from_user.id)
    await show_profile_text_request(message)


@router.callback_query(F.data == "profile")
async def profile_handler(callback: types.CallbackQuery):
    user = await asyncio.to_thread(db.user, callback.from_user.id)
    if user is None:
        raise OperationError("Для создания профиля напишите /start.")
    status = "Пройдена" if user["verified"] else "Не пройдена"
    caption = (
        f"📂 Профиль: #{user['tg_id']}\n"
        f"✅ Верификация: <b>{status}</b>\n"
        f"📅 Вы были зарегистрированы <b>{escape(str(user['date_regist']))}</b>\n"
        f"💵 Баланс: <b>{escape(str(user['balance']))} ₽</b>"
    )
    await show_screen(callback, caption, reply_markup=back_to_profile_inline_keyboard)
