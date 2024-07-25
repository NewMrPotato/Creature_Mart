# базы данных
import sqlite3

# aiogram
from aiogram.enums import ParseMode
from aiogram.types import CallbackQuery, FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.media_group import MediaGroupBuilder
from aiogram import types

# импорт внутри проекта
from handlers.users.different_functions import delete_last_messages
from handlers.users.profile import show_profile_callback_request
from keyboards.inline.inline_buttons import elemental_spirits_inline_keyboard, start_market_inline_keyboard, \
    celestial_guardians_inline_keyboard, mystical_beasts_inline_keyboard, legendary_creatures_inline_keyboard, aquatic_wonders_inline_keyboard, \
    mythical_figures_inline_keyboard, cryptic_oddities_inline_keyboard, dreamweavers_inline_keyboard
from loader import router, dp, bot


# Возращаем пользователя в market
@router.callback_query(lambda query: query.data == "back_to_market")
async def back_to_market(callback: types.CallbackQuery):
    # Удаляем сообщения
    await delete_last_messages(callback.message)

    # Показываем market
    caption = f'🐲<b> Creatures маркетплейс</b>\n\n' \
              f'<i>Пожалуйста, выберите коллекцию</i>'
    await callback.message.answer(caption, parse_mode=ParseMode.HTML, reply_markup=start_market_inline_keyboard)


@router.callback_query(lambda query: query.data == "creature_market")
async def creature_collection_handler(callback: types.CallbackQuery):
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

        caption = f'🐲<b> Creatures маркетплейс</b>\n\n' \
                  f'<i>Пожалуйста, выберите коллекцию</i>'
        await callback.message.answer(caption, parse_mode=ParseMode.HTML, reply_markup=start_market_inline_keyboard)
    else:
        await callback.message.answer('Вы были добавлены в черный список⚫️ \n\nДля вас доступ к боту запрещен!')


# Показ creature пользователя
@router.callback_query(lambda query: query.data == "my_creature")
async def creature_collection_handler(callback: types.CallbackQuery):
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
        # Подключение к базе данных
        conn = sqlite3.connect('data/database/database_shop.sqlite')
        cursor = conn.cursor()

        # Получаем данные по указанному идентификатору
        cursor.execute("SELECT * FROM user_creature WHERE user_id = ?", (callback.from_user.id,))
        result_from_user_creature = cursor.fetchone()

        # Закрываем соединение с базой данных
        cursor.close()
        conn.close()

        if result_from_user_creature[1] == '':
            await callback.message.answer('У вас нет Creatures🤷')
        else:
            await delete_last_messages(callback.message, number=2)

            # Подключение к базе данных
            conn = sqlite3.connect('data/database/database_shop.sqlite')
            cursor = conn.cursor()

            items = []

            for creature_id in result_from_user_creature[1].split(','):
                # Получаем данные по указанному идентификатору
                cursor.execute("SELECT * FROM creatures WHERE id = ?", (creature_id,))
                result_from_creatures = cursor.fetchone()
                items.append(result_from_creatures)

            # Закрываем соединение с базой данных
            cursor.close()
            conn.close()

            # Создаем словарь с элементами управления инлайн-кнопками
            item_buttons = {}

            for item in items:
                collection = item[2].replace('_', ' ')

                # Создаем кнопку для каждого предмета
                button = types.InlineKeyboardButton(
                    text=f'{collection} #{item[1]} ({item[5]} RUB)',  # Текст кнопки
                    callback_data=str(
                        ['m', item[0]])
                    .replace('[', '').replace(']', '').replace(',', '/').replace('\'', '')
                    .replace(' ', '').replace('n', '').replace('\\', '').replace('\"', '')
                )

                # Добавляем кнопку в словарь
                item_buttons[item[0]] = button

            buttons = []

            for item_dict in item_buttons.values():
                buttons.append([item_dict])

            buttons.append([InlineKeyboardButton(text="⬅️Назад", callback_data='back_to_profile')])

            my_creature_keyboard = types.InlineKeyboardMarkup(row_width=2, inline_keyboard=buttons,
                                              resize_keyboard=True,
                                              one_time_keyboard=True,
                                              input_field_placeholder="Choice a button",
                                              selective=True)

            caption = f'🐲<b>Creatures в вашей коллекции:</b>'

            await callback.message.answer(caption, parse_mode=ParseMode.HTML, reply_markup=my_creature_keyboard)
    else:
        await callback.message.answer('Вы были добавлены в черный список⚫️ \n\nДля вас доступ к боту запрещен!')


# Надпись для коллекций
collection_caption = f'🐲<b> Creatures маркетплейс</b>\n\n' \
          f'<i>Пожалуйста, выберите Creature</i>'


# celestial_guardians
# ---{
@router.callback_query(lambda query: query.data == "celestial_guardians_collection")
async def creature_collection_handler(callback: types.CallbackQuery):
    await delete_last_messages(callback.message)

    await callback.message.answer(collection_caption, parse_mode=ParseMode.HTML, reply_markup=celestial_guardians_inline_keyboard)


# Возращаем пользователя в коллекцию celestial_guardians
@router.callback_query(lambda query: query.data == "back_to_celestialguardians")
async def back_to_creature_collection(callback: types.CallbackQuery):
    # Удаляем сообщения
    await delete_last_messages(callback.message, number=2)

    await callback.message.answer(collection_caption, parse_mode=ParseMode.HTML, reply_markup=celestial_guardians_inline_keyboard)
# ---}


# mystical_beasts
# ---{
@router.callback_query(lambda query: query.data == "mystical_beasts_collection")
async def creature_collection_handler(callback: types.CallbackQuery):
    await delete_last_messages(callback.message)

    await callback.message.answer(collection_caption, parse_mode=ParseMode.HTML, reply_markup=mystical_beasts_inline_keyboard)


# Возращаем пользователя в коллекцию mystical_beasts
@router.callback_query(lambda query: query.data == "back_to_mysticalbeasts")
async def back_to_creature_collection(callback: types.CallbackQuery):
    # Удаляем сообщения
    await delete_last_messages(callback.message, number=2)

    await callback.message.answer(collection_caption, parse_mode=ParseMode.HTML, reply_markup=mystical_beasts_inline_keyboard)
# ---}


# legendary_creatures
# ---{
@router.callback_query(lambda query: query.data == "legendary_creatures_collection")
async def creature_collection_handler(callback: types.CallbackQuery):
    await delete_last_messages(callback.message)

    await callback.message.answer(collection_caption, parse_mode=ParseMode.HTML, reply_markup=legendary_creatures_inline_keyboard)


# Возращаем пользователя в коллекцию legendary_creatures
@router.callback_query(lambda query: query.data == "back_to_legendarycreatures")
async def back_to_creature_collection(callback: types.CallbackQuery):
    # Удаляем сообщения
    await delete_last_messages(callback.message, number=2)

    await callback.message.answer(collection_caption, parse_mode=ParseMode.HTML, reply_markup=legendary_creatures_inline_keyboard)
# ---}


# aquatic_wonders
# ---{
@router.callback_query(lambda query: query.data == "aquatic_wonders_collection")
async def creature_collection_handler(callback: types.CallbackQuery):
    await delete_last_messages(callback.message)

    await callback.message.answer(collection_caption, parse_mode=ParseMode.HTML, reply_markup=aquatic_wonders_inline_keyboard)


# Возращаем пользователя в коллекцию aquatic_wonders
@router.callback_query(lambda query: query.data == "back_to_aquaticwonders")
async def back_to_creature_collection(callback: types.CallbackQuery):
    # Удаляем сообщения
    await delete_last_messages(callback.message, number=2)

    await callback.message.answer(collection_caption, parse_mode=ParseMode.HTML, reply_markup=aquatic_wonders_inline_keyboard)
# ---}


# mythical_figures
# ---{
@router.callback_query(lambda query: query.data == "mythical_figures_collection")
async def creature_collection_handler(callback: types.CallbackQuery):
    await delete_last_messages(callback.message)

    await callback.message.answer(collection_caption, parse_mode=ParseMode.HTML, reply_markup=mythical_figures_inline_keyboard)


# Возращаем пользователя в коллекцию mythical_figures
@router.callback_query(lambda query: query.data == "back_to_mythicalfigures")
async def back_to_creature_collection(callback: types.CallbackQuery):
    # Удаляем сообщения
    await delete_last_messages(callback.message, number=2)

    await callback.message.answer(collection_caption, parse_mode=ParseMode.HTML, reply_markup=mythical_figures_inline_keyboard)
# ---}


# cryptic_oddities
# ---{
@router.callback_query(lambda query: query.data == "cryptic_oddities_collection")
async def creature_collection_handler(callback: types.CallbackQuery):
    await delete_last_messages(callback.message)

    await callback.message.answer(collection_caption, parse_mode=ParseMode.HTML, reply_markup=cryptic_oddities_inline_keyboard)


# Возращаем пользователя в коллекцию cryptic_oddities
@router.callback_query(lambda query: query.data == "back_to_crypticoddities")
async def back_to_creature_collection(callback: types.CallbackQuery):
    # Удаляем сообщения
    await delete_last_messages(callback.message, number=2)

    await callback.message.answer(collection_caption, parse_mode=ParseMode.HTML, reply_markup=cryptic_oddities_inline_keyboard)
# ---}


# dreamweavers
# ---{
@router.callback_query(lambda query: query.data == "dreamweavers_collection")
async def creature_collection_handler(callback: types.CallbackQuery):
    await delete_last_messages(callback.message)

    await callback.message.answer(collection_caption, parse_mode=ParseMode.HTML, reply_markup=dreamweavers_inline_keyboard)


# Возращаем пользователя в коллекцию dreamweavers
@router.callback_query(lambda query: query.data == "back_to_dreamweavers")
async def back_to_creature_collection(callback: types.CallbackQuery):
    # Удаляем сообщения
    await delete_last_messages(callback.message, number=2)

    await callback.message.answer(collection_caption, parse_mode=ParseMode.HTML, reply_markup=dreamweavers_inline_keyboard)
# ---}


# elemental_spirits
# ---{
@router.callback_query(lambda query: query.data == "elemental_spirits_collection")
async def creature_collection_handler(callback: types.CallbackQuery):
    await delete_last_messages(callback.message)

    await callback.message.answer(collection_caption, parse_mode=ParseMode.HTML, reply_markup=elemental_spirits_inline_keyboard)


# Возращаем пользователя в коллекцию elemental_spirits
@router.callback_query(lambda query: query.data == "back_to_elementalspirits")
async def back_to_creature_collection(callback: types.CallbackQuery):
    # Удаляем сообщения
    await delete_last_messages(callback.message, number=2)

    await callback.message.answer(collection_caption, parse_mode=ParseMode.HTML, reply_markup=elemental_spirits_inline_keyboard)
# ---}


# Обработка Callback Query и Отправка Описания creature
@router.callback_query()
async def item_creature_handler(callback: CallbackQuery):
    # Получаем данные из обратного вызова
    callback_data = callback.data

    callback_data = callback_data.split('/')

    if callback_data[0] == 'market':
        # Удаляем сообщения
        await delete_last_messages(callback.message)
        # Подключение к базе данных
        conn = sqlite3.connect('data/database/database_shop.sqlite')
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM creatures WHERE id = ?", (callback_data[-1],))
        creature_info = cursor.fetchone()

        # Закрываем соединение с базой данных
        cursor.close()
        conn.close()

        creature_name = creature_info[3].replace('_', ' ')
        creature_collection = creature_info[2].replace('_', ' ')
        creature_place = creature_info[6].replace('_', ' ')

        caption = f'🐲{creature_name} #{creature_info[1]}\n\n' \
                  f'Информация\n' \
                  f'┠ Коллекция: {creature_collection}\n' \
                  f'┠ Место обитания: {creature_place}\n' \
                  f'┖ Цвет: {creature_info[4]}\n\n' \
                  f'Цена: {creature_info[5]} RUB'

        album_builder = MediaGroupBuilder(
            caption=caption
        )
        album_builder.add(
            type="photo",
            media=FSInputFile(f"data/images/creatures/{callback_data[-1]}.jpg")
        )
        await callback.message.answer_media_group(
            # Не забудьте вызвать build()
            media=album_builder.build()
        )

        # Подключение к базе данных
        conn = sqlite3.connect('data/database/database_shop.sqlite')
        cursor = conn.cursor()

        # Получаем данные по указанному идентификатору
        cursor.execute("SELECT * FROM user_creature WHERE user_id = ?", (callback.from_user.id,))
        result_from_user_creature = cursor.fetchone()

        # Закрываем соединение с базой данных
        cursor.close()
        conn.close()

        if result_from_user_creature[1] is None:
            # Кнопки для технической поддержки
            creature_buy_buttons = [
                [
                    InlineKeyboardButton(
                        text="⬅️Назад",
                        callback_data=f'back_to_{callback_data[1].replace("_", "").lower()}'
                    ),
                    InlineKeyboardButton(
                        text="🛒Купить",
                        callback_data=f'buy/{callback_data[6]}/{callback_data[4]}/{callback.from_user.id}'
                    )
                ]
            ]
        elif callback_data[-1] in result_from_user_creature[1].split(','):
            # Кнопки для технической поддержки
            creature_buy_buttons = [
                [
                    InlineKeyboardButton(
                        text="⬅️Назад",
                        callback_data=f'back_to_{creature_info[2].replace("_", "").lower()}'
                    ),
                    InlineKeyboardButton(
                        text="🛒Продать",
                        callback_data=f'sell/{callback_data[-1]}/{creature_info[5]}/{callback.from_user.id}'
                    )
                ]
            ]
        else:
            # Кнопки для технической поддержки
            creature_buy_buttons = [
                [
                    InlineKeyboardButton(
                        text="⬅️Назад",
                        callback_data=f'back_to_{creature_info[2].replace("_", "").lower()}'
                    ),
                    InlineKeyboardButton(
                        text="🛒Купить",
                        callback_data=f'buy/{callback_data[-1]}/{creature_info[5]}/{callback.from_user.id}'
                    )
                ]
            ]

        creature_buy_inline_keyboard = InlineKeyboardMarkup(inline_keyboard=creature_buy_buttons,
                                                           resize_keyboard=True,
                                                           one_time_keyboard=True,
                                                           input_field_placeholder="Choice a button",
                                                           selective=True)

        await callback.message.answer('Выберите действие:', parse_mode=ParseMode.HTML, reply_markup=creature_buy_inline_keyboard)

    elif callback_data[0] == 'buy':
        # Подключение к базе данных
        conn = sqlite3.connect('data/database/database_shop.sqlite')
        cursor = conn.cursor()

        # Получаем данные по указанному идентификатору
        cursor.execute("SELECT * FROM users WHERE tg_id = ?", (callback.from_user.id,))
        result = cursor.fetchone()

        # Закрываем соединение с базой данных
        cursor.close()
        conn.close()

        if int(result[1]) < int(callback_data[2]):
            await callback.message.answer('У вас недостаточно средств на баланс❌')
        else:
            # Удаляем сообщения
            await delete_last_messages(callback.message, number=2)

            await callback.message.answer('Успешная покупка! Поздравляю, теперь вы владелец этим Creature🎉')

            # Возращаем пользователя в маркет
            caption = f'🐲<b> Creatures маркетплейс</b>\n\n' \
                      f'<i>Пожалуйста, выберите коллекцию</i>'
            await callback.message.answer(caption, parse_mode=ParseMode.HTML, reply_markup=start_market_inline_keyboard)

            # Подключение к базе данных
            conn = sqlite3.connect('data/database/database_shop.sqlite')
            cursor = conn.cursor()

            # Изменяем баланс данные по указанному идентификатору
            cursor.execute(f"""
                UPDATE users
                SET balance = {int(result[1]) - int(callback_data[2])}
                WHERE tg_id = {callback.from_user.id};
            """)

            # Получаем данные по указанному идентификатору
            cursor.execute("SELECT * FROM user_creature WHERE user_id = ?", (callback.from_user.id,))
            result_from_user_creature = cursor.fetchone()

            if result_from_user_creature[1] != '' and result_from_user_creature[1] is not None:
                user_creatures = result_from_user_creature[1].split(',')
                user_creatures.append(int(callback_data[1]))
            else:
                user_creatures = [int(callback_data[1])]

            creature_list_str = ','.join(str(creature_id) for creature_id in user_creatures)

            # Изменяем creatures по указанному идентификатору
            cursor.execute(f"UPDATE user_creature SET creature_list = \'{creature_list_str}\' WHERE user_id = {callback.from_user.id};")

            # Подтверждаем изменения
            conn.commit()

            # Закрываем соединение с базой данных
            cursor.close()
            conn.close()

    elif callback_data[0] == 'm':
        # Удаляем сообщения
        await delete_last_messages(callback.message, number=2)

        # Подключение к базе данных
        conn = sqlite3.connect('data/database/database_shop.sqlite')
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM creatures WHERE id = ?", (callback_data[-1],))
        creature_info = cursor.fetchone()

        # Закрываем соединение с базой данных
        cursor.close()
        conn.close()

        creature_name = creature_info[3].replace('_', ' ')
        creature_collection = creature_info[2].replace('_', ' ')
        creature_place = creature_info[6].replace('_', ' ')

        caption = f'🐲{creature_name} #{creature_info[1]}\n\n' \
                  f'Информация\n' \
                  f'┠ Коллекция: {creature_collection}\n' \
                  f'┠ Место обитания: {creature_place}\n' \
                  f'┖ Цвет: {creature_info[4]}'

        album_builder = MediaGroupBuilder(
            caption=caption
        )
        album_builder.add(
            type="photo",
            media=FSInputFile(f"data/images/creatures/{callback_data[-1]}.jpg")

        )
        await callback.message.answer_media_group(
            # Не забудьте вызвать build()
            media=album_builder.build()
        )

        # Подключение к базе данных
        conn = sqlite3.connect('data/database/database_shop.sqlite')
        cursor = conn.cursor()

        # Получаем данные по указанному идентификатору
        cursor.execute("SELECT * FROM user_creature WHERE user_id = ?", (callback.from_user.id,))
        result_from_user_creature = cursor.fetchone()

        # Закрываем соединение с базой данных
        cursor.close()
        conn.close()

        # Кнопки для Управлением своими creature
        creature_my_buttons = [
            [
                InlineKeyboardButton(
                    text="⬅️Назад",
                    callback_data='my_creature'
                ),
                InlineKeyboardButton(
                    text="🛒Продать",
                    callback_data=f'sell/{callback_data[-1]}/{callback.from_user.id}'
                )
            ]
        ]

        creature_my_inline_keyboard = InlineKeyboardMarkup(inline_keyboard=creature_my_buttons,
                                                       resize_keyboard=True,
                                                       one_time_keyboard=True,
                                                       input_field_placeholder="Choice a button",
                                                       selective=True)

        await callback.message.answer('Выберите действие:', parse_mode=ParseMode.HTML,
                                      reply_markup=creature_my_inline_keyboard)

    elif callback_data[0] == 'sell':
        # Подключение к базе данных
        conn = sqlite3.connect('data/database/database_shop.sqlite')
        cursor = conn.cursor()

        # Получение цены на существо
        cursor.execute("SELECT price FROM creatures WHERE id = ?", (callback_data[1],))
        creature_price = int(cursor.fetchone()[0])

        # Обновление баланса
        cursor.execute("SELECT * FROM users WHERE tg_id = ?", (callback.from_user.id,))
        result = cursor.fetchone()

        cursor.execute("UPDATE users SET balance = ? WHERE tg_id = ?",
                       (int(result[1]) + creature_price, callback.from_user.id))
        conn.commit()

        # Обновление коллекции существ
        cursor.execute("SELECT * FROM user_creature WHERE user_id = ?", (callback.from_user.id,))
        result = cursor.fetchone()

        creatures_own_ids = result[1].split(',')

        for i in range(len(creatures_own_ids)):
            print(int(creatures_own_ids[i]), callback_data[1])
            if int(creatures_own_ids[i]) == int(callback_data[1]):
                del creatures_own_ids[i]
                break

        cursor.execute("UPDATE user_creature SET creature_list = ? WHERE user_id = ?",
                       (str(creatures_own_ids).replace(' ', '').replace('[', '').replace(']', '').replace('\'', ''),
                        callback.from_user.id))
        conn.commit()

        # Закрываем соединение с базой данных
        cursor.close()
        conn.close()

        await delete_last_messages(callback.message, number=2)

        await callback.message.answer(f'Creature продан за {creature_price} рублей✅')

        await show_profile_callback_request(callback)
