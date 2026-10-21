import asyncio
from html import escape

from aiogram import F, types

from config import MINIMUM_AMOUNT
from database import OperationError
from handlers.users.navigation import show_screen
from keyboards.inline.inline_buttons import (
    back_to_profile_inline_keyboard,
    checking_payment_inline_keyboard,
)
from loader import db, router, settings


@router.callback_query(F.data == "deposit")
async def deposit_handler(callback: types.CallbackQuery):
    await asyncio.to_thread(db.begin_flow, callback.from_user.id, "depositing")
    await show_screen(
        callback,
        f"💸<b>Пополнение баланса</b>\n\nМинимальная сумма: {MINIMUM_AMOUNT} RUB\nВведите сумму для пополнения",
        reply_markup=back_to_profile_inline_keyboard,
    )


@router.callback_query(F.data == "way_to_increase_balance_bankcard")
async def bankcard_handler(callback: types.CallbackQuery):
    state, data = await asyncio.to_thread(db.session, callback.from_user.id)
    if state != "deposit_ready":
        raise OperationError("Сумма пополнения не задана. Начните пополнение заново.")
    caption = (
        f"💸<b>Пополнение баланса</b>\n\nОплатите <b>{data['amount']} RUB</b> по реквизитам, которые выдаст "
        f'<a href="{escape(settings.support_url, quote=True)}">ТЕХ. ПОДДЕРЖКА</a>\n\n'
        "После пополнения предоставьте квитанцию в техническую поддержку."
    )
    await show_screen(callback, caption, reply_markup=checking_payment_inline_keyboard)
