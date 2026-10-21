import asyncio
from html import escape

from aiogram import F, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config import BASE_DIR
from database import OperationError
from handlers.users.navigation import show_screen
from handlers.users.profile import show_profile_callback_request
from keyboards.inline.inline_buttons import COLLECTIONS, get_keyboard, start_market_inline_keyboard
from loader import db, router


@router.callback_query(F.data.in_({"back_to_market", "creature_market"}))
async def show_market(callback: types.CallbackQuery, notice=""):
    await show_screen(
        callback,
        (f"{escape(notice)}\n\n" if notice else "")
        + "🐲<b>Creatures маркетплейс</b>\n\n<i>Пожалуйста, выберите коллекцию</i>",
        reply_markup=start_market_inline_keyboard,
    )


@router.callback_query(F.data == "my_creature")
async def show_owned(callback: types.CallbackQuery):
    owned = await asyncio.to_thread(db.owned, callback.from_user.id)
    items = await asyncio.to_thread(db.creatures)
    items = [item for item in items if item["id"] in owned]
    await show_screen(
        callback,
        "🐲<b>Creatures в вашей коллекции:</b>" if items else "У вас нет доступных Creatures🤷",
        reply_markup=get_keyboard(items, prefix="m", back="back_to_profile"),
    )


COLLECTION_CALLBACKS = {
    key: collection
    for collection in COLLECTIONS
    for key in (
        collection.lower() + "_collection",
        "back_to_" + collection.replace("_", "").lower(),
    )
}


@router.callback_query(F.data.in_(COLLECTION_CALLBACKS))
async def show_collection(callback: types.CallbackQuery):
    items = await asyncio.to_thread(db.creatures, COLLECTION_CALLBACKS[callback.data])
    await show_screen(
        callback,
        "🐲<b>Creatures маркетплейс</b>\n\n<i>Пожалуйста, выберите Creature</i>",
        reply_markup=get_keyboard(items),
    )


@router.callback_query(F.data.regexp(r"^(market|m)/[0-9]+$"))
async def show_creature(callback: types.CallbackQuery):
    prefix, value = callback.data.split("/")
    if len(value) > 10:
        raise OperationError("Некорректный идентификатор Creature.")
    creature = await asyncio.to_thread(db.creature, int(value))
    owned = await asyncio.to_thread(db.owned, callback.from_user.id)
    if prefix == "m" and creature["id"] not in owned:
        raise OperationError("Этот Creature больше не принадлежит вам.")
    action = "sell" if creature["id"] in owned else "buy"
    token = await asyncio.to_thread(db.offer, callback.from_user.id, creature["id"], action)
    back = (
        "my_creature"
        if prefix == "m"
        else "back_to_" + creature["collection"].replace("_", "").lower()
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⬅️Назад", callback_data=back),
                InlineKeyboardButton(
                    text="🛒Продать" if action == "sell" else "🛒Купить",
                    callback_data=f"{action}/{token}",
                ),
            ],
            [InlineKeyboardButton(text="🏠В меню", callback_data="back_to_profile")],
        ]
    )
    caption = (
        f"🐲{escape(creature['name'].replace('_', ' '))} #{creature['number']}\n\n"
        f"Коллекция: {escape(creature['collection'].replace('_', ' '))}\n"
        f"Место обитания: {escape(creature['place'].replace('_', ' '))}\n"
        f"Цвет: {escape(creature['color'])}\n\nЦена: {escape(str(creature['price']))} RUB"
    )
    photo = BASE_DIR / f"data/images/creatures/{creature['id']}.jpg"
    await show_screen(
        callback, caption, reply_markup=keyboard, photo=photo if photo.is_file() else None
    )


@router.callback_query(F.data.regexp(r"^(buy|sell)/[0-9a-f]{24}$"))
async def trade_creature(callback: types.CallbackQuery):
    action, token = callback.data.split("/")
    price = await asyncio.to_thread(db.trade, callback.from_user.id, token, action)
    if action == "buy":
        await show_market(callback, notice="Успешная покупка! Creature добавлен в вашу коллекцию🎉")
    else:
        await show_profile_callback_request(callback, notice=f"Creature продан за {price} RUB✅")


@router.callback_query()
async def unknown_callback(callback: types.CallbackQuery):
    if callback.data not in {"<<", ">>", "1/1"}:
        raise OperationError("Эта кнопка устарела. Откройте меню: /start.")
