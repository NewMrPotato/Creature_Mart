# базы данных
import sqlite3

# aiogram
from aiogram.enums import ParseMode
from aiogram import types

# импорт внутри проекта
from handlers.users.different_functions import delete_last_messages
from handlers.users.start import minimal_sum  # turn_on_output_money_processing
from keyboards.inline import back_to_profile_inline_keyboard, back_to_profile_inline_keyboard2
from loader import router, dp, bot


# Показываем окно с минимальной суммой вывода
@router.callback_query(lambda query: query.data == "output_money")
async def deposit_handler(callback: types.CallbackQuery):
    # Подключение к базе данных
    conn = sqlite3.connect('data/database/database_shop.sqlite')
    cursor = conn.cursor()

    # Обновление баланса
    cursor.execute("SELECT status FROM users WHERE tg_id = ?", (callback.from_user.id,))

    result = cursor.fetchone()
    user_status = result[0]

    # Закрываем соединение с базой данных
    cursor.close()
    conn.close()

    if user_status != 'blacklist':
        await delete_last_messages(callback.message)

        # Установите соединение с базой данных
        conn = sqlite3.connect('data/database/database_shop.sqlite')
        cursor = conn.cursor()

        # Выполните запрос
        cursor.execute("""UPDATE users SET status = ? WHERE tg_id = ?""", ('outputmoney', callback.from_user.id))

        # Сохраните изменения в базе данных
        conn.commit()

        # Закройте соединение с базой данных
        cursor.close()
        conn.close()

        caption = f'💸<b>Вывод средств</b>\n\n' \
                  f'<b>Минимальная сумма вывода:</b>\n' \
                  f'{minimal_sum} RUB\n\n' \
                  f'<i>Введите сумму для вывода</i>'

        await callback.message.answer(caption, parse_mode=ParseMode.HTML, reply_markup=back_to_profile_inline_keyboard)
    else:
        await callback.message.answer('Вы были добавлены в черный список⚫️ \n\nДля вас доступ к боту запрещен!')
