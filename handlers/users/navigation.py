import asyncio
import logging
from pathlib import Path

from aiogram import types
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.types import FSInputFile, InputMediaPhoto

from keyboards.inline.inline_buttons import back_to_profile_inline_keyboard
from loader import db

logger = logging.getLogger(__name__)


async def show_screen(
    event: types.Message | types.CallbackQuery,
    text: str,
    reply_markup: types.InlineKeyboardMarkup | None = None,
    *,
    photo: Path | None = None,
    parse_mode: str | None = "HTML",
):
    message = event.message if isinstance(event, types.CallbackQuery) else event
    if not isinstance(message, types.Message):
        return
    bot = event.bot
    if reply_markup is None:
        reply_markup = back_to_profile_inline_keyboard
    chat_id = message.chat.id
    current = await asyncio.to_thread(db.ui_message, chat_id)
    if (
        current is None
        and isinstance(event, types.CallbackQuery)
        and message.from_user
        and message.from_user.id == bot.id
    ):
        current = {
            "message_id": message.message_id,
            "kind": "photo" if message.photo else "text",
        }
    kind = "photo" if photo else "text"
    if current and (photo or current["kind"] == "text"):
        try:
            if photo:
                await bot.edit_message_media(
                    chat_id=chat_id,
                    message_id=current["message_id"],
                    media=InputMediaPhoto(
                        media=FSInputFile(photo), caption=text, parse_mode=parse_mode
                    ),
                    reply_markup=reply_markup,
                )
            else:
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=current["message_id"],
                    text=text,
                    parse_mode=parse_mode,
                    reply_markup=reply_markup,
                )
        except TelegramBadRequest as error:
            description = error.message.lower()
            if "message is not modified" in description:
                await asyncio.to_thread(db.save_ui_message, chat_id, current["message_id"], kind)
                return
            if not any(
                reason in description
                for reason in (
                    "message to edit not found",
                    "message can't be edited",
                    "message_id_invalid",
                )
            ):
                raise
        else:
            await asyncio.to_thread(db.save_ui_message, chat_id, current["message_id"], kind)
            return

    # Telegram cannot remove media to turn a photo back into a text message.
    # Send the replacement first so a failed request never removes the usable screen.
    if photo:
        sent = await bot.send_photo(
            chat_id,
            FSInputFile(photo),
            caption=text,
            parse_mode=parse_mode,
            reply_markup=reply_markup,
        )
    else:
        sent = await bot.send_message(
            chat_id,
            text,
            parse_mode=parse_mode,
            reply_markup=reply_markup,
        )
    await asyncio.to_thread(db.save_ui_message, chat_id, sent.message_id, kind)
    if current:
        try:
            await bot.delete_message(chat_id, current["message_id"])
        except TelegramAPIError as error:
            logger.warning("Previous screen could not be removed: %s", type(error).__name__)
