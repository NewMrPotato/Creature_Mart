# aiogram
from aiogram import types

# импорт внутри проекта
from loader import router, dp, bot


async def delete_last_messages(message: types.Message, number=1):
    # Извлекаем идентификаторы чата и сообщений
    chat_id = message.chat.id
    message_ids = [message.message_id - i for i in range(0, number)]

    # Удаляем сообщения
    await bot.delete_messages(chat_id=chat_id, message_ids=message_ids)

