import asyncio
import logging
import sqlite3

from aiogram import BaseMiddleware, types
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest

from database import OperationError
from handlers.users.navigation import show_screen
from loader import db

logger = logging.getLogger(__name__)


class AccessMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        is_callback = isinstance(event, types.CallbackQuery)
        message = event.message if is_callback else event
        answered = False
        if not isinstance(message, types.Message) or not event.from_user:
            if is_callback:
                await self.answer_callback(event)
            return
        if message.chat.type != "private" or message.chat.id != event.from_user.id:
            if is_callback:
                await self.answer_callback(event)
            return
        try:
            user = await asyncio.to_thread(db.user, event.from_user.id)
            if user and user["status"] == "blacklist":
                raise OperationError("Вы в чёрном списке. Доступ к боту запрещён.")
            registration_callback = is_callback and event.data in {
                "🐶",
                "🐼",
                "🐵",
                "🐸",
                "🐷",
                "🐱",
                "user_acceptation",
            }
            if is_callback and user is None and not registration_callback:
                raise OperationError("Для создания профиля напишите /start.")
            return await handler(event, data)
        except OperationError as error:
            if is_callback:
                await self.answer_callback(event, str(error))
                answered = True
            else:
                await self.reply(message, str(error))
        except sqlite3.Error:
            logger.exception("Database operation failed")
            if is_callback:
                await self.answer_callback(
                    event, "Не удалось выполнить операцию. Попробуйте позже."
                )
                answered = True
            else:
                await self.reply(message, "Не удалось выполнить операцию. Попробуйте позже.")
        except TelegramAPIError as error:
            # Exceptions may embed message text, requisites or confirmation codes.
            logger.warning("Telegram request failed: %s", type(error).__name__)
            if is_callback:
                await self.answer_callback(
                    event, "Не удалось обновить экран. Откройте меню: /menu."
                )
                answered = True
        finally:
            if is_callback and not answered:
                await self.answer_callback(event)

    @staticmethod
    async def answer_callback(callback, text=None):
        try:
            await callback.answer(text=text, show_alert=bool(text))
        except TelegramBadRequest:
            logger.info("Callback acknowledgement expired")
        except TelegramAPIError as error:
            logger.warning("Callback acknowledgement failed: %s", type(error).__name__)

    @staticmethod
    async def reply(message, text):
        try:
            await show_screen(message, text, parse_mode=None)
        except sqlite3.Error:
            logger.exception("Could not load the screen for an error response")
            try:
                await message.answer(text, parse_mode=None)
            except TelegramAPIError as error:
                logger.warning("Error response delivery failed: %s", type(error).__name__)
        except TelegramAPIError as error:
            logger.warning("Error response delivery failed: %s", type(error).__name__)


async def send_text_chunks(message, text):
    for start in range(0, len(text), 4000):
        await message.answer(text[start : start + 4000], parse_mode=None)
