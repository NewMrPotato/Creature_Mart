import asyncio

from aiogram import F, types

from config import MINIMUM_AMOUNT
from handlers.users.navigation import show_screen
from keyboards.inline.inline_buttons import back_to_profile_inline_keyboard
from loader import db, router


@router.callback_query(F.data == "output_money")
async def withdrawal_handler(callback: types.CallbackQuery):
    await asyncio.to_thread(db.begin_flow, callback.from_user.id, "outputmoney")
    await show_screen(
        callback,
        f"💸<b>Вывод средств</b>\n\nМинимальная сумма: {MINIMUM_AMOUNT} RUB\nВведите сумму для вывода",
        reply_markup=back_to_profile_inline_keyboard,
    )
