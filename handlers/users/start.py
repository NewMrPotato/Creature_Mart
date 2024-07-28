# базы данных
import sqlite3

# aiogram
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram import types, F

# импорт внутри проекта
from handlers.users.different_functions import delete_last_messages
from handlers.users.profile import show_profile_text_request
from keyboards.default.reply_buttons import profile_keyboard
from keyboards.inline import capture_keyboard
from keyboards.inline.inline_buttons import emojis, user_acceptation_inline_keyboard, \
    way_to_increase_balance_inline_keyboard, back_to_profile_buttons, back_to_profile_inline_keyboard
from loader import router, dp, bot

# другие
import random
import os


with open('data/text/config.txt', 'r') as f:
    lines = f.readlines()

minimal_sum = 52

# Переменная для отслеживания временной суммы
sum_to_increase_balance = 0

elected_emoji = '🟨'
user_acceptation_url = lines[3].split('\\')[0].replace(' ', '')

outputting_money_user_id = None
acceptation_outputting_money_code = None

seller_id = None
selling_price = None
selling_creature_id = None

admins_id = [int(i) for i in lines[1].split('\\')[0].replace(' ', '').split(',')]

# Это можете убрать
#admins_id.append(int(os.getenv("ID")))

first_tutor_id = int(lines[4].split('\\')[0].replace(' ', '').split(',')[0])
second_tutor_id = int(lines[4].split('\\')[0].replace(' ', '').split(',')[1])
first_tutor_link = lines[2].split('\\')[0].replace(' ', '').split(',')[0]
second_tutor_link = lines[2].split('\\')[0].replace(' ', '').split(',')[1]
acceptation_selling_code = None


# Функции для изменения sum_to_increase_balance
# {
async def turn_off_sum_balance():
    global sum_to_increase_balance
    sum_to_increase_balance = 0


async def get_sum_balance():
    return sum_to_increase_balance

# }


def link_to_website():
    return f'📃Пользоваетльское соглашение\n\n' \
           f'Нажимая кнопку для принятия, вы соглащаетесь с <a href="{user_acceptation_url}">пользовательским соглашением</a>'


async def send_message_with_link(chat_id):
    linked_text = link_to_website()
    await bot.send_message(chat_id, linked_text, parse_mode=ParseMode.HTML,
                           reply_markup=user_acceptation_inline_keyboard)


# Команда для тестирование чего либо
@dp.message(Command("test"))
async def cmd_settimer(message: Message, command: CommandObject):
    await message.answer('English or Spanish?')


# Обработка сообщений
@router.message()
async def message_handler(message: types.Message):
    global sum_to_increase_balance, acceptation_selling_code, seller_id, selling_price,\
        selling_creature_id, outputting_money_user_id, acceptation_outputting_money_code

    # Подключение к базе данных
    conn = sqlite3.connect('data/database/database_shop.sqlite')
    cursor = conn.cursor()

    # Обновление баланса
    cursor.execute("SELECT status FROM users WHERE tg_id = ?", (message.from_user.id,))

    result = cursor.fetchone()
    user_status = ''

    if result is not None:
        user_status = result[0]

    # Закрываем соединение с базой данных
    cursor.close()
    conn.close()

    # Обработка для админки
    if message.text == '/admin' and message.from_user.id in admins_id:
        await message.answer(f'Возможности админов:\n\n'
                             f'1) Чтобы пополнить баланс пользователю вам нужно будет ввести без пробелов следующую команду:\n'
                             f'bi/телеграм id/сумма пополнения\n\n'
                             f'2) Чтобы получить данные о всех пользователях введите команду:\n'
                             f'users\n\n'
                             f'3)  Чтобы получить данные о Creature пользователя введите команду:\n'
                             f'creature/телеграм id\n\n'
                             f'4) Чтобы добавить пользователя в черный список введите команду:\n'
                             f'blacklist/телеграм id\n'
                             f'(Чтобы добавить в белый список, нужно ввести эту команду повторно)\n\n'
                             f'5) Чтобы верифицировать пользователя нужно ввести команду:\n'
                             f'verify/телеграм id')

    # Получение любой таблицы из базы данных
    elif message.text.split('/')[0] == 'gettable' and message.from_user.id in admins_id:

        conn = sqlite3.connect('data/database/database_shop.sqlite')
        cursor = conn.cursor()

        cursor.execute(f"SELECT * FROM {message.text.split('/')[1]}")
        rows = cursor.fetchall()

        table_str = ""
        for row in rows:
            table_str += " | ".join(str(cell) for cell in row) + "\n"

        conn.close()

        MAX_MESSAGE_LENGTH = 4000

        if len(table_str) > MAX_MESSAGE_LENGTH:
            parts = [table_str[i:i + MAX_MESSAGE_LENGTH] for i in range(0, len(table_str), MAX_MESSAGE_LENGTH)]
        else:
            parts = [table_str]

        for part in parts:
            await message.answer(part)

    # Получение данных о пользователях
    elif message.text.split('/')[0] == 'users' and message.from_user.id in admins_id:

        conn = sqlite3.connect('data/database/database_shop.sqlite')
        cursor = conn.cursor()

        cursor.execute(f"SELECT * FROM users")
        rows = cursor.fetchall()

        table_str = ''

        for row in rows:
            status = ''
            if not (bool(row[3])):
                status = '🔴Не верифицирован'
            else:
                status = '🟢Верифицирован'

            table_str += f'Профиль: #{row[0]}\n' \
                         f'Баланс: {row[1]} RUB\n' \
                         f'Верификация: {status}\n' \
                         f'Номер карты: {row[4]}\n' \
                         f'Username: @{row[5]} \n\n'

        conn.close()

        MAX_MESSAGE_LENGTH = 4000

        if len(table_str) > MAX_MESSAGE_LENGTH:
            parts = [table_str[i:i + MAX_MESSAGE_LENGTH] for i in range(0, len(table_str), MAX_MESSAGE_LENGTH)]
        else:
            parts = [table_str]

        for part in parts:
            await message.answer(part)

    # Получение данных о creatures пользователя
    elif message.text.split('/')[0] == 'creature' and message.from_user.id in admins_id:
        # Будет возникать ошибка либо при неправильном id либо при отсутствии creature
        try:
            conn = sqlite3.connect('data/database/database_shop.sqlite')
            cursor = conn.cursor()

            cursor.execute(f"SELECT creature_list FROM user_creature WHERE user_id = ?", (int(message.text.split('/')[1]),))
            creature_ids = cursor.fetchall()[0][0].split(',')

            creature_info = []

            for i in creature_ids:
                cursor.execute(f"SELECT * FROM creatures WHERE id = ?", (int(i),))
                result = cursor.fetchall()[0]

                creature_info.append([str(j) for j in result])

            user_id_loc = message.text.split('/')[1]
            table_str = f'Профиль: #{user_id_loc}\n\n'

            for creature in creature_info:
                table_str += f'Creature id: {creature[0]}\n' \
                             f'Номер Creature: {creature[1]}\n' \
                             f'Коллекция: {creature[2]}\n' \
                             f'Название: {creature[3]}\n' \
                             f'Цвет: {creature[4]}\n' \
                             f'Цена: {creature[5]} RUB\n\n'

            conn.close()

            MAX_MESSAGE_LENGTH = 4000

            if len(table_str) > MAX_MESSAGE_LENGTH:
                parts = [table_str[i:i + MAX_MESSAGE_LENGTH] for i in range(0, len(table_str), MAX_MESSAGE_LENGTH)]
            else:
                parts = [table_str]

            for part in parts:
                await message.answer(part)
        except Exception as e:
            await message.answer('Во время получения информации произошло ошибка❌\n\n'
                                 'Скорее всего, это связано с некорректным id пользователя или с отсутствием creature у пользователя')

    # Обработчика для пополнения баланса админом
    elif message.text.split('/')[0] == 'bi' and message.from_user.id in admins_id:
        # Подключение к базе данных
        conn = sqlite3.connect('data/database/database_shop.sqlite')
        cursor = conn.cursor()

        # Обновление баланса
        cursor.execute("SELECT * FROM users WHERE tg_id = ?", (int(message.text.split('/')[1]),))
        result = cursor.fetchone()

        cursor.execute("UPDATE users SET balance = ? WHERE tg_id = ?",
                       (int(result[1]) + int(message.text.split('/')[2]), int(message.text.split('/')[1])))
        conn.commit()

        # Закрываем соединение с базой данных
        cursor.close()
        conn.close()

        await message.answer('Баланс был успешно пополнен✅')

    # Обработчика для верификации пользователя
    elif message.text.split('/')[0] == 'verify' and message.from_user.id in admins_id:
        # Подключение к базе данных
        conn = sqlite3.connect('data/database/database_shop.sqlite')
        cursor = conn.cursor()

        # Обновление статуса верификации пользователя
        cursor.execute("UPDATE users SET verified = ? WHERE tg_id = ?",
                       (1, int(message.text.split('/')[1])))
        conn.commit()

        # Закрываем соединение с базой данных
        cursor.close()
        conn.close()

        await message.answer('Пользователь был успешно верифицирован✅')

    # Обработчика для верификации пользователя
    elif message.text.split('/')[0] == 'blacklist' and message.from_user.id in admins_id and int(message.text.split('/')[1]) not in admins_id:
        # Подключение к базе данных
        conn = sqlite3.connect('data/database/database_shop.sqlite')
        cursor = conn.cursor()

        # Обновление баланса
        cursor.execute("SELECT status FROM users WHERE tg_id = ?", (int(message.text.split('/')[1]),))

        result = cursor.fetchone()
        bl_user_status = result[0]

        # Заносим пользователя в черный список, если он уже в нем не находится
        if bl_user_status != 'blacklist':
            # Выполните запрос
            cursor.execute("""UPDATE users SET status = ? WHERE tg_id = ?""", ('blacklist', int(message.text.split('/')[1])))
            conn.commit()

            await message.answer('Пользователь был успешно занесен в черный список⚫️')
        # Если же он уже в черном списке, то заносим его в белый
        else:
            # Выполните запрос
            cursor.execute("""UPDATE users SET status = ? WHERE tg_id = ?""",
                           ('default', int(message.text.split('/')[1])))
            conn.commit()

            await message.answer('Пользователь был успешно занесен в белый список⚪️')

        # Закрываем соединение с базой данных
        cursor.close()
        conn.close()

    # Обработчика для /getid
    elif message.text == '/getid':
        await message.answer(f'Ваш телеграм id: {message.from_user.id}')

    # Проверка на вывод с баланса
    elif user_status == 'blacklist':
        await message.answer('Вы были добавлены в черный список⚫️ \n\n'
                             'Для вас доступ к боту запрещен!')

    # Обработчика для /start
    elif message.text == '/start':
        # Подключаемся к базе данных
        conn = sqlite3.connect('data/database/database_shop.sqlite')
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM users WHERE tg_id = ?", (message.from_user.id,))
        count = cursor.fetchone()[0]

        # Закрываем соединение с базой данных
        cursor.close()
        conn.close()

        if not (count > 0):  # проверка на существование пользователя в базе даннах
            # Создаём случайную капчу
            random_emoji = random.choice(emojis)

            global elected_emoji
            elected_emoji = random_emoji

            # Формируем сообщение с капчей
            caption = f"Выберите животное: {random_emoji}"

            await message.answer(caption, reply_markup=capture_keyboard)
        else:
            await message.answer('У вас уже есть профиль в этом боте✅', reply_markup=profile_keyboard)

    # Подтверждение продажи
    elif len(message.text.split(',')) == 2 and (message.from_user.id == first_tutor_id or message.from_user.id == second_tutor_id):

        acceptation_selling_code = ''.join([str(random.randint(1, 9)) for i in range(4)])
        seller_id = int(message.text.split(',')[0])
        selling_creature_id = int(message.text.split(',')[1])

        await message.answer('Ваш запрос принять✅')
        await message.answer(f'Отправьте данный код продавцу: {acceptation_selling_code}')

        if message.from_user.id == first_tutor_id:
            await bot.send_message(seller_id, f'Нашли покупателя😌 \n\nНапишите человеку по ссылке ниже и попросите <b><i>код подтверждения</i></b> \n\n{first_tutor_link}', parse_mode=ParseMode.HTML)
        else:
            await bot.send_message(seller_id, f'Нашли покупателя😌 \n\nНапишите человеку по ссылке ниже и попросите <b><i>код подтверждения</i></b> \n\n{second_tutor_link}', parse_mode=ParseMode.HTML)

        await bot.send_message(seller_id, f'Подтвердите продажу Creature, введите код, который вы получили от покупателя',
                               parse_mode=ParseMode.HTML)

    # Подтверждение продажи
    elif message.from_user.id == seller_id:
        if message.text == acceptation_selling_code:
            await message.answer(f'Creature продан за {selling_price} рублей✅')

            # Подключение к базе данных
            conn = sqlite3.connect('data/database/database_shop.sqlite')
            cursor = conn.cursor()

            # Обновление баланса
            cursor.execute("SELECT * FROM users WHERE tg_id = ?", (message.from_user.id,))
            result = cursor.fetchone()

            cursor.execute("UPDATE users SET balance = ? WHERE tg_id = ?", (int(result[1]) + selling_price, message.from_user.id))
            conn.commit()

            # Обновление коллекции creature
            cursor.execute("SELECT * FROM user_creature WHERE user_id = ?", (message.from_user.id,))
            result = cursor.fetchone()

            creature_own_ids = result[1].split(',')

            for i in range(len(creature_own_ids)):
                print(int(creature_own_ids[i]), selling_creature_id)
                if int(creature_own_ids[i]) == selling_creature_id:
                    del creature_own_ids[i]
                    break

            cursor.execute("UPDATE user_creature SET creature_list = ? WHERE user_id = ?",
                           (str(creature_own_ids).replace(' ', '').replace('[', '').replace(']', '').replace('\'', ''), message.from_user.id))
            conn.commit()

            # Закрываем соединение с базой данных
            cursor.close()
            conn.close()

            # Очищаем все данные после продажи
            acceptation_selling_code = None
            selling_price = None
            seller_id = None
            selling_creature_id = None

            # После продажи показываем профиль
            await show_profile_text_request(message)

        else:
            await message.answer('Неверный код подтверждения продажи❌')
            await message.answer('Продажа Creature остановлена!')

            # Очищаем все данные после продажи
            acceptation_selling_code = None
            selling_price = None
            seller_id = None
            selling_creature_id = None

    # Подтверждение вывода денег
    elif message.from_user.id == outputting_money_user_id:
        if message.text == acceptation_outputting_money_code:
            await message.answer(f'Заявка обрабатывается, ожидайте подтверждения✅')

            acceptation_outputting_money_code = None
            outputting_money_user_id = None
        else:
            await message.answer('Неверный код подтверждения продажи❌')
            await message.answer('Заявка на вывод средств была остановлена!')

            acceptation_outputting_money_code = None
            outputting_money_user_id = None

    # Проверка на ввод депозита
    elif user_status == 'depositing':
        deposit = message.text

        if deposit.isdigit():
            sum_to_increase_balance = int(deposit)

        # Проверка на коректность ввода
        if not (deposit.isdigit()) or not (sum_to_increase_balance >= minimal_sum):
            await message.answer('Некоректное ввод для депозита❌\n\n'
                                 f'Проверьте, что сумма не ниже {minimal_sum} RUB и что число правильно записано')
        else:
            #await turn_off_depositing()

            # Установите соединение с базой данных
            conn = sqlite3.connect('data/database/database_shop.sqlite')
            cursor = conn.cursor()

            # Выполните запрос
            cursor.execute("""UPDATE users SET status = ? WHERE tg_id = ?""", ('default', message.from_user.id))

            # Сохраните изменения в базе данных
            conn.commit()

            # Закройте соединение с базой данных
            cursor.close()
            conn.close()

            caption = f'💸<b>Пополнение баланса</b>\n\n' \
                      f'<b>Сумма:</b>\n' \
                      f'{sum_to_increase_balance} RUB\n\n' \
                      f'<i>Выберите откуда вы хотете внести средства</i>'
            await message.answer(caption, parse_mode=ParseMode.HTML,
                                 reply_markup=way_to_increase_balance_inline_keyboard)

    # Проверка на вывод с баланса
    elif user_status == 'outputmoney':
        # Подключение к базе данных
        conn = sqlite3.connect('data/database/database_shop.sqlite')
        cursor = conn.cursor()

        # Получаем данные по указанному идентификатору
        cursor.execute("SELECT * FROM users WHERE tg_id = ?", (message.from_user.id,))
        result = cursor.fetchone()

        # Закрываем соединение с базой данных
        cursor.close()
        conn.close()

        output_money = message.text

        if output_money.isdigit():
            sum_to_increase_balance = int(output_money)

        # Проверка на коректность ввода
        if not (output_money.isdigit()) or not (sum_to_increase_balance >= minimal_sum):
            await message.answer('Некоректное ввод для вывода❌\n\n'
                                 f'Проверьте, что сумма не ниже {minimal_sum} RUB и что число правильно записано')
        # Хватает ли баланса для вывода
        elif result[1] < sum_to_increase_balance:
            await message.answer('Сумма вывода превышает баланс, вывод отклонен❌\n\n')

            # Установите соединение с базой данных
            conn = sqlite3.connect('data/database/database_shop.sqlite')
            cursor = conn.cursor()

            # Выполните запрос
            cursor.execute("""UPDATE users SET status = ? WHERE tg_id = ?""", ('default', message.from_user.id))

            # Сохраните изменения в базе данных
            conn.commit()

            # Закройте соединение с базой данных
            cursor.close()
            conn.close()

            await show_profile_text_request(message)
        else:
            # Установите соединение с базой данных
            conn = sqlite3.connect('data/database/database_shop.sqlite')
            cursor = conn.cursor()

            # Выполните запрос
            cursor.execute("""UPDATE users SET status = ? WHERE tg_id = ?""", ('requisites', message.from_user.id))

            # Сохраните изменения в базе данных
            conn.commit()

            # Закройте соединение с базой данных
            cursor.close()
            conn.close()

            caption = f'💸<b>Вывод средств</b>\n\n' \
                      f'<i>Введите реквизиты</i>\n\n' \
                      f'<b>Доступно:</b>\n' \
                      f'Card'

            await message.answer(caption, parse_mode=ParseMode.HTML,
                                 reply_markup=back_to_profile_inline_keyboard)

    # Проверка на получение реквизитов
    elif user_status == 'requisites':
        # Подключение к базе данных
        conn = sqlite3.connect('data/database/database_shop.sqlite')
        cursor = conn.cursor()

        cursor.execute("UPDATE users SET number_card = ? WHERE tg_id = ?", (message.text, message.from_user.id))
        conn.commit()

        cursor.execute("SELECT * FROM users WHERE tg_id = ?", (message.from_user.id,))
        result = cursor.fetchone()

        # Закрываем соединение с базой данных
        cursor.close()
        conn.close()

        outputting_money_user_id = message.from_user.id

        # Установите соединение с базой данных
        conn = sqlite3.connect('data/database/database_shop.sqlite')
        cursor = conn.cursor()

        # Выполните запрос
        cursor.execute("""UPDATE users SET status = ? WHERE tg_id = ?""", ('default', message.from_user.id))

        # Сохраните изменения в базе данных
        conn.commit()

        # Закройте соединение с базой данных
        cursor.close()
        conn.close()

        await bot.send_message(first_tutor_id,
                               f'Пользователь {message.from_user.username} (telegram id: {message.from_user.id})'
                               f' c реквизитами {result[4]} подал заявку на сумму вывода {sum_to_increase_balance} RUB'
                               , parse_mode=ParseMode.HTML)

        acceptation_outputting_money_code = ''.join([str(random.randint(1, 9)) for i in range(4)])

        await bot.send_message(first_tutor_id,
                               f'Отправьте данный код пользователю: {acceptation_outputting_money_code}',
                               parse_mode=ParseMode.HTML)

        await message.answer('Ваша заявка в обработке, свяжитесь с куратором', parse_mode=ParseMode.HTML)
        await message.answer('Введите код подтвержения от вашего куратора', parse_mode=ParseMode.HTML)

    # Проверка на получение реквизитов
    elif user_status == 'selling':
        # Установите соединение с базой данных
        conn = sqlite3.connect('data/database/database_shop.sqlite')
        cursor = conn.cursor()

        # Выполните запрос
        cursor.execute("""UPDATE users SET status = ? WHERE tg_id = ?""", ('default', message.from_user.id))

        # Сохраните изменения в базе данных
        conn.commit()

        # Закройте соединение с базой данных
        cursor.close()
        conn.close()

        selling_money = message.text

        # Проверка на коректность ввода
        if not (selling_money.isdigit()):
            await message.answer('Некоректное ввод цены для creature❌\n'
                                 'Проверьте, что число правильно записано\n\n'
                                 'Запрос отклонен, попробуйте еще раз!')

            # Подключение к базе данных
            conn = sqlite3.connect('data/database/database_shop.sqlite')
            cursor = conn.cursor()

            # Найти строку по user_id, где price пустой
            query = '''
                SELECT user_id, creature_id, price
                FROM exchanges
                WHERE user_id = ? AND price = ''
            '''

            cursor.execute(query, (message.from_user.id,))
            row = cursor.fetchone()

            # Удалить строку
            if row:
                query = '''
                    DELETE FROM exchanges
                    WHERE user_id = ? AND creature_id = ?
                '''
                cursor.execute(query, (row[0], row[1]))
                conn.commit()

            cursor.close()
            conn.close()

            await show_profile_text_request(message)
        else:
            await message.answer('Ваша заявка одобрена! Покупатель в поиске🔎')

            selling_price = int(selling_money)

            conn = sqlite3.connect('data/database/database_shop.sqlite')
            cursor = conn.cursor()

            cursor.execute(f"SELECT * FROM exchanges WHERE user_id = ?", (message.from_user.id,))
            result = cursor.fetchall()

            print(result)

            try:
                id_creature = result[-1][1]
            except Exception as e:
                id_creature = result[1]

            cursor.execute("SELECT * FROM creatures WHERE id = ?", (id_creature,))
            result = cursor.fetchone()

            if selling_price <= 10000:
                await bot.send_message(first_tutor_id, f'Пользователь {message.from_user.username} (telegram id: {message.from_user.id}) выставил на продажу за {selling_money} RUB Creature (creature id: {id_creature}):\n\n'
                                             f'🐲 <b>Creature {result[2]} #{result[1]}</b>\n\n'
                                             f'<b>Информация</b>\n'
                                             f'<b>┠ </b>Коллекция: <b>{result[2]}</b>\n'
                                             f'<b>┠ </b>Название: <b>{result[3]}</b>\n'
                                             f'<b>┖ </b>Цвет: <b>{result[4]}\n</b>'
                                             f'<i>Цена в боте: {result[5]}</i>', parse_mode=ParseMode.HTML)

                await bot.send_message(first_tutor_id, f'Для того чтобы ответить на запрос, нужно отправить этому боту следующие сообщение: telegram id, creature id', parse_mode=ParseMode.HTML)
            else:
                await bot.send_message(second_tutor_id,
                                       f'Пользователь {message.from_user.username} (telegram id: {message.from_user.id}) выставил на продажу за {selling_money} RUB Creature (creature id: {id_creature}):\n\n'
                                       f'🐲 <b>Creature {result[2]} #{result[1]}</b>\n\n'
                                       f'<b>Информация</b>\n'
                                       f'<b>┠ </b>Коллекция: <b>{result[2]}</b>\n'
                                       f'<b>┠ </b>Название: <b>{result[3]}</b>\n'
                                       f'<b>┖ </b>Цвет: <b>{result[4]}\n</b>'
                                       f'<i>Цена в боте: {result[5]}</i>', parse_mode=ParseMode.HTML)

                await bot.send_message(second_tutor_id,
                                       f'Для того чтобы ответить на запрос, нужно отправить этому боту следующие сообщение: telegram id, creature id',
                                       parse_mode=ParseMode.HTML)

            # Обновить ячейку в таблице по id пользователя и имени
            query = '''
                UPDATE exchanges
                SET price = ?
                WHERE user_id = ? AND price = ''
            '''

            cursor.execute(query, (selling_money, message.from_user.id))
            conn.commit()

            cursor.close()
            conn.close()

            await show_profile_text_request(message)


# Обработчики для ответа капчи
@router.callback_query(lambda query: query.data == "🐼")
async def capture_animal_handler(callback: types.CallbackQuery):
    if "🐼" == elected_emoji:
        await delete_last_messages(callback.message)
        await send_message_with_link(chat_id=callback.message.chat.id)
    else:
        await delete_last_messages(callback.message)
        await callback.message.answer('Капча пройдена неверно!')


@router.callback_query(lambda query: query.data == "🐵")
async def capture_animal_handler(callback: types.CallbackQuery):
    if "🐵" == elected_emoji:
        await delete_last_messages(callback.message)
        await send_message_with_link(chat_id=callback.message.chat.id)
    else:
        await delete_last_messages(callback.message)
        await callback.message.answer('Капча пройдена неверно!')


@router.callback_query(lambda query: query.data == "🐸")
async def capture_animal_handler(callback: types.CallbackQuery):
    if "🐸" == elected_emoji:
        await delete_last_messages(callback.message)
        await send_message_with_link(chat_id=callback.message.chat.id)
    else:
        await delete_last_messages(callback.message)
        await callback.message.answer('Капча пройдена неверно!')


@router.callback_query(lambda query: query.data == "🐷")
async def capture_animal_handler(callback: types.CallbackQuery):
    if "🐷" == elected_emoji:
        await delete_last_messages(callback.message)
        await send_message_with_link(chat_id=callback.message.chat.id)
    else:
        await delete_last_messages(callback.message)
        await callback.message.answer('Капча пройдена неверно!')


@router.callback_query(lambda query: query.data == "🐱")
async def capture_animal_handler(callback: types.CallbackQuery):
    if "🐱" == elected_emoji:
        await delete_last_messages(callback.message)
        await send_message_with_link(chat_id=callback.message.chat.id)
    else:
        await delete_last_messages(callback.message)
        await callback.message.answer('Капча пройдена неверно!')


@router.callback_query(lambda query: query.data == "🐶")
async def capture_animal_handler(callback: types.CallbackQuery):
    if "🐶" == elected_emoji:
        await delete_last_messages(callback.message)
        await send_message_with_link(chat_id=callback.message.chat.id)
    else:
        await delete_last_messages(callback.message)
        await callback.message.answer('Капча пройдена неверно!')
