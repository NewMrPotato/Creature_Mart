import asyncio
import logging
import sys

from aiogram.exceptions import TelegramAPIError, TelegramRetryAfter

logger = logging.getLogger(__name__)


async def deliver_notifications(bot, db):
    for notification in await asyncio.to_thread(db.pending_notifications):
        try:
            await bot.send_message(notification["chat_id"], notification["text"], parse_mode=None)
        except TelegramRetryAfter as error:
            logger.warning("Notification delivery rate limited")
            await asyncio.sleep(error.retry_after)
            break
        except TelegramAPIError as error:
            logger.warning("Notification delivery failed: %s", type(error).__name__)
        else:
            await asyncio.to_thread(db.mark_notification_sent, notification["id"])


async def notification_worker(bot, db):
    while True:
        try:
            await deliver_notifications(bot, db)
        except Exception as error:
            logger.error("Notification worker failed: %s", type(error).__name__)
        await asyncio.sleep(10)


async def on_startup():
    from handlers import dp
    from loader import bot, db

    try:
        await asyncio.to_thread(db.initialize)
        worker = asyncio.create_task(notification_worker(bot, db))
        try:
            await dp.start_polling(bot, close_bot_session=False)
        finally:
            worker.cancel()
            await asyncio.gather(worker, return_exceptions=True)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(on_startup())
