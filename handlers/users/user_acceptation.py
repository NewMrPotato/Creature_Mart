# базы данных
import sqlite3
# aiogram
from aiogram import types

# импорт внутри проекта
from handlers.users.profile import show_profile_callback_request
from handlers.users.start import delete_last_messages
from keyboards.default.reply_buttons import profile_keyboard
from loader import router, dp, bot

# время
import datetime


@router.callback_query(lambda query: query.data == "user_acceptation")
async def high_evaluation_handler(callback: types.CallbackQuery):
    # Подключаемся к базе данных
    conn = sqlite3.connect('data/database/database_shop.sqlite')
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users WHERE tg_id = ?", (callback.from_user.id,))
    count = cursor.fetchone()[0]

    # Закрываем соединение с базой данных
    cursor.close()
    conn.close()

    if not (count > 0):  # проверка на существование пользователя в базе даннах
        await delete_last_messages(callback.message)

        await callback.message.answer('Вы приняли соглашение!')
        await callback.message.answer('Ваш профиль был создан👤')

        # Подключение к базе данных
        conn = sqlite3.connect('data/database/database_shop.sqlite')
        cursor = conn.cursor()

        # Получаем текущую дату в виде объекта datetime
        today = datetime.datetime.now()

        # Данные нового пользователя
        user_id = callback.from_user.id
        balance = 0
        date_regist = today.date()
        verified = False
        number_card = '0'
        username = callback.from_user.username
        status = 'default'

        # Если ник у пользователя скрыт, то он будет неизвестен
        if username is None:
            username = 'UNKNOWN'

        # Выполнение запроса на добавление нового пользователя
        cursor.execute("INSERT INTO users (tg_id, balance, date_regist, verified, number_card, username, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (user_id, balance, date_regist, verified, number_card, username, status))
        print(f"ID: {user_id}, Balance: {balance}, Date registered: {date_regist}, Verified: {verified},"
              f" Number card: {number_card}, Username: {username}, Status: {status}")

        cursor.execute(
            "INSERT INTO user_creature (user_id, creature_list) VALUES (?, ?)",
            (user_id, ''))

        # Подтверждаем изменения
        conn.commit()

        # Закрытие соединения с базой данных
        conn.close()

        # Показываем профиль
        await show_profile_callback_request(callback)
    elif count > 0:
        await callback.message.answer('У вас уже есть профиль в этом боте✅', reply_markup=profile_keyboard)
