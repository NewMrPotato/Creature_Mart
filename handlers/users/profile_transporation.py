# базы данных
import sqlite3

# aiogram
from aiogram import types

# импорт внутри проекта
from handlers.users.different_functions import delete_last_messages
from handlers.users.profile import show_profile_callback_request
from loader import router, dp, bot


# Возращаем пользователя в профиль
@router.callback_query(lambda query: query.data == "back_to_profile")
async def back_to_profile(callback: types.CallbackQuery):
    # Установите соединение с базой данных
    conn = sqlite3.connect('data/database/database_shop.sqlite')
    cursor = conn.cursor()

    # Выполните запрос
    cursor.execute("""UPDATE users SET status = ? WHERE tg_id = ?""", ('default', callback.from_user.id))

    # Сохраните изменения в базе данных
    conn.commit()

    # Закройте соединение с базой данных
    cursor.close()
    conn.close()

    # Удаляем сообщения
    await delete_last_messages(callback.message)

    # Показываем профиль пользователя
    await show_profile_callback_request(callback)


# Возращаем пользователя в профиль
@router.callback_query(lambda query: query.data == "back_to_profile2")
async def back_to_profile2(callback: types.CallbackQuery):
    # Установите соединение с базой данных
    conn = sqlite3.connect('data/database/database_shop.sqlite')
    cursor = conn.cursor()

    # Выполните запрос
    cursor.execute("""UPDATE users SET status = ? WHERE tg_id = ?""", ('default', callback.from_user.id))

    # Сохраните изменения в базе данных
    conn.commit()

    # Закройте соединение с базой данных
    cursor.close()
    conn.close()

    # Удаляем сообщения
    await delete_last_messages(callback.message, number=2)

    # Показываем профиль пользователя
    await show_profile_callback_request(callback)

