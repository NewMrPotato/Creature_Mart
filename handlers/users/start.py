import asyncio
import secrets
from html import escape

from aiogram import F, types
from aiogram.filters import Command, CommandStart

from database import OperationError, amount
from handlers.users.different_functions import send_text_chunks
from handlers.users.navigation import show_screen
from handlers.users.profile import show_profile_text_request
from keyboards.inline.inline_buttons import (
    back_to_profile_inline_keyboard,
    capture_keyboard,
    emojis,
    user_acceptation_inline_keyboard,
    way_to_increase_balance_inline_keyboard,
)
from loader import db, router, settings


@router.message(CommandStart())
async def start_handler(message: types.Message):
    user = await asyncio.to_thread(db.user, message.from_user.id)
    if user:
        await asyncio.to_thread(db.cancel, message.from_user.id)
        await show_profile_text_request(message)
    else:
        emoji = secrets.choice(emojis)
        await asyncio.to_thread(db.start_captcha, message.from_user.id, emoji)
        await show_screen(message, f"Выберите животное: {emoji}", reply_markup=capture_keyboard)


@router.message(Command("cancel", "menu"))
async def cancel_handler(message: types.Message):
    await asyncio.to_thread(db.cancel, message.from_user.id)
    await show_profile_text_request(message)


@router.message(Command("getid"))
async def get_id(message: types.Message):
    await message.answer(f"Ваш телеграм id: {message.from_user.id}")


@router.message(Command("admin"))
async def admin_help(message: types.Message):
    if message.from_user.id not in settings.admin_ids:
        raise OperationError("Команда доступна только администраторам.")
    await message.answer(
        "Возможности администраторов:\n\n"
        "bi/telegram_id/сумма — пополнить баланс\n"
        "users — список пользователей\n"
        "creature/telegram_id — коллекция пользователя\n"
        "blacklist/telegram_id — переключить чёрный список\n"
        "verify/telegram_id — верифицировать пользователя\n"
        "gettable/таблица — посмотреть таблицу",
        parse_mode=None,
    )


@router.callback_query(F.data.in_(emojis))
async def captcha_handler(callback: types.CallbackQuery):
    await asyncio.to_thread(db.solve_captcha, callback.from_user.id, callback.data)
    await show_screen(
        callback,
        f'📃Нажимая кнопку, вы принимаете <a href="{escape(settings.agreement_url, quote=True)}">пользовательское соглашение</a>.',
        reply_markup=user_acceptation_inline_keyboard,
    )


@router.message()
async def message_handler(message: types.Message):
    if not message.text:
        await show_screen(message, "Отправьте текстовое сообщение. Для возврата в меню: /cancel.")
        return
    text = message.text.strip()
    user_id = message.from_user.id
    command = text.split("/", 1)[0]
    if command in {"bi", "users", "creature", "createre", "blacklist", "verify", "gettable"}:
        reply = await asyncio.to_thread(
            db.admin_command, user_id, settings.admin_ids, text, message.chat.id, message.message_id
        )
        await send_text_chunks(message, reply)
        return
    if user_id in settings.tutor_ids and "," in text:
        parts = text.split(",")
        if len(parts) != 2:
            raise OperationError("Формат: telegram_id,creature_id")
        await asyncio.to_thread(
            db.prepare_exchange,
            user_id,
            settings.tutor_ids,
            settings.tutor_links,
            amount(parts[0].strip()),
            amount(parts[1].strip()),
            message.chat.id,
            message.message_id,
        )
        await show_screen(
            message, "Запрос принят. Куратору будет отправлен код, продавцу — инструкция."
        )
        return
    user = await asyncio.to_thread(db.user, user_id)
    if user is None:
        raise OperationError("Для создания профиля напишите /start.")
    state, _ = await asyncio.to_thread(db.session, user_id)
    if state == "depositing":
        value = await asyncio.to_thread(db.set_amount, user_id, text, state)
        await show_screen(
            message,
            f"💸Пополнение баланса\n\nСумма: {value} RUB\nВыберите способ оплаты:",
            reply_markup=way_to_increase_balance_inline_keyboard,
        )
    elif state == "outputmoney":
        await asyncio.to_thread(db.set_amount, user_id, text, state)
        await show_screen(
            message, "Введите реквизиты карты:", reply_markup=back_to_profile_inline_keyboard
        )
    elif state == "requisites":
        await asyncio.to_thread(db.request_withdrawal, user_id, text, settings.tutor_ids[0])
        await show_screen(
            message,
            "Заявка создана. Свяжитесь с куратором и введите полученный код подтверждения.",
            reply_markup=back_to_profile_inline_keyboard,
        )
    elif state == "withdrawal_code":
        confirmed = await asyncio.to_thread(db.confirm_withdrawal, user_id, text)
        await show_screen(
            message,
            "Заявка подтверждена, ожидайте обработки куратором✅"
            if confirmed
            else "Неверный код или недостаточный баланс. Заявка отменена.",
        )
    elif state == "sale_code":
        price = await asyncio.to_thread(db.confirm_exchange, user_id, text)
        await show_profile_text_request(
            message,
            notice=f"Creature продан за {price} RUB✅"
            if price is not None
            else "Неверный код. Продажа остановлена.",
        )
    elif user["status"] == "selling":
        await asyncio.to_thread(db.price_exchange, user_id, text, settings.tutor_ids)
        await show_screen(message, "Ваша заявка принята. Покупатель в поиске🔎")
    elif user["status"] in {"depositing", "outputmoney", "requisites"}:
        await asyncio.to_thread(db.cancel, user_id)
        await show_profile_text_request(
            message, notice="Прежний диалог не содержит суммы. Начните операцию заново."
        )
    else:
        await show_profile_text_request(message)
