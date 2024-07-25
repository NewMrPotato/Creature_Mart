# базы данных
import sqlite3

# aiogram
from aiogram.enums import ParseMode
from aiogram import types

# импорт внутри проекта
from handlers.users.different_functions import delete_last_messages
from handlers.users.start import get_sum_balance, minimal_sum
from keyboards.inline.inline_buttons import back_to_profile_inline_keyboard, checking_payment_inline_keyboard, \
    maintenance_link
from loader import router, dp, bot


# Показываем окно с минимальной суммой депозита
@router.callback_query(lambda query: query.data == "deposit")
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
        cursor.execute("""UPDATE users SET status = ? WHERE tg_id = ?""", ('depositing', callback.from_user.id))

        # Сохраните изменения в базе данных
        conn.commit()

        # Закройте соединение с базой данных
        cursor.close()
        conn.close()

        caption = f'💸<b>Пополнение баланса</b>\n\n' \
                  f'<b>Минимальная сумма:</b>\n' \
                  f'{minimal_sum} RUB\n\n' \
                  f'<i>Введите сумму для пополнения</i>'

        await callback.message.answer(caption, parse_mode=ParseMode.HTML, reply_markup=back_to_profile_inline_keyboard)
    else:
        await callback.message.answer('Вы были добавлены в черный список⚫️ \n\nДля вас доступ к боту запрещен!')


# Показываем окно с номером карты для депозита
@router.callback_query(lambda query: query.data == "way_to_increase_balance_bankcard")
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

        # Получение суммы для депозита
        sum_to_pay = await get_sum_balance()

        caption = f'💸<b>Пополнение баланса</b>\n\n' \
                  f'Оплатите <b>{sum_to_pay} RUB</b> по реквизитам, которые выдаст \n' \
                  f'<a href="{maintenance_link}"><b><i>ТЕХ. ПОДДЕРЖКА</i></b></a>\n' \
                  f'\n' \
                  f'🧾<i>После пополнения баланса предоставьте квитанцию в техническую поддержку</i>'
        await callback.message.answer(caption, parse_mode=ParseMode.HTML, reply_markup=checking_payment_inline_keyboard)
    else:
        await callback.message.answer('Вы были добавлены в черный список⚫️ \n\nДля вас доступ к боту запрещен!')
