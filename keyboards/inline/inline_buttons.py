# базы данных
import sqlite3

# aiogram
from aiogram import types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


with open('data/text/config.txt', 'r') as f:
    lines = f.readlines()

maintenance_link = lines[5].split('\\')[0].replace(' ', '')


# Функция для получения списка предметов из базы данных
def get_items_from_db(collection):
    # Соединяемся с базой данных
    conn = sqlite3.connect('data/database/database_shop.sqlite')
    cursor = conn.cursor()

    # Запрашиваем список всех предметов
    cursor.execute("SELECT * FROM creatures WHERE collection = ?", (collection,))

    # Получаем список кортежей со свойствами предметов
    items = cursor.fetchall()

    # Закрываем соединение с базой данных
    cursor.close()
    conn.close()

    return items


# Функция для создания инлайн-кнопок для каждого предмета
def create_inline_buttons(items):
    # Создаем словарь с элементами управления инлайн-кнопками
    item_buttons = {}

    for item in items:
        collection = item[2].replace('_', ' ')

        # Создаем кнопку для каждого предмета
        button = types.InlineKeyboardButton(
            text=f'{collection} #{item[1]} ({item[5]} RUB)',  # Текст кнопки
            callback_data=str(['market', item[0]])
            .replace('[', '').replace(']', '').replace(',', '/').replace('\'', '').replace(' ', '').replace('n', '').replace('\\', '').replace('\"', '')
        )

        # Добавляем кнопку в словарь
        item_buttons[item[0]] = button

    return item_buttons


def get_keyboard(collection):
    # Получаем список предметов из базы данных
    items = get_items_from_db(collection)

    # Создаем инлайн-кнопки для каждого предмета
    item_buttons = create_inline_buttons(items)

    buttons = []

    for item_dict in item_buttons.values():
        buttons.append([item_dict])

    buttons.append([InlineKeyboardButton(text="⬅️Назад", callback_data='creature_market')])

    return types.InlineKeyboardMarkup(row_width=2, inline_keyboard=buttons,
                                               resize_keyboard=True,
                                               one_time_keyboard=True,
                                               input_field_placeholder="Choice a button",
                                               selective=True)


# Создаем клавиатуру с инлайн-кнопками для коллекций creature
celestial_guardians_inline_keyboard = get_keyboard('Celestial_Guardians')
mystical_beasts_inline_keyboard = get_keyboard('Mystical_Beasts')
legendary_creatures_inline_keyboard = get_keyboard('Legendary_Creatures')
aquatic_wonders_inline_keyboard = get_keyboard('Aquatic_Wonders')
mythical_figures_inline_keyboard = get_keyboard('Mythical_Figures')
cryptic_oddities_inline_keyboard = get_keyboard('Cryptic_Oddities')
dreamweavers_inline_keyboard = get_keyboard('Dreamweavers')
elemental_spirits_inline_keyboard = get_keyboard('Elemental_Spirits')

# Кнопки для маркета
start_market_buttons = [
    [
        InlineKeyboardButton(
            text="Celestial Guardians",
            callback_data='celestial_guardians_collection'
        ),
        InlineKeyboardButton(
            text="Mystical Beasts",
            callback_data='mystical_beasts_collection'
        ),
    ],
    [
        InlineKeyboardButton(
            text="Legendary Creatures",
            callback_data='legendary_creatures_collection'
        ),
        InlineKeyboardButton(
            text="Aquatic Wonders",
            callback_data='aquatic_wonders_collection'
        ),
    ],
    [
        InlineKeyboardButton(
            text="Mythical Figures",
            callback_data='mythical_figures_collection'
        ),
        InlineKeyboardButton(
            text="Dreamweavers",
            callback_data='dreamweavers_collection'
        ),
    ],
    [
        InlineKeyboardButton(
            text="Cryptic Oddities",
            callback_data='cryptic_oddities_collection'
        ),
        InlineKeyboardButton(
            text="Elemental Spirits",
            callback_data='elemental_spirits_collection'
        ),
    ],
    [
        InlineKeyboardButton(
            text="<<",
            callback_data='<<'
        ),
        InlineKeyboardButton(
            text="1/1",
            callback_data='1/1'
        ),
        InlineKeyboardButton(
            text=">>",
            callback_data='>>'
        ),
    ],
    [
        InlineKeyboardButton(
            text="⬅️Назад",
            callback_data='back_to_profile'
        ),
    ],
]
start_market_inline_keyboard = InlineKeyboardMarkup(inline_keyboard=start_market_buttons,
                                                    resize_keyboard=True,
                                                    one_time_keyboard=True,
                                                    input_field_placeholder="Choice a button",
                                                    selective=True)

# Кнопки для технической поддержки
maintenance_buttons = [
    [
        InlineKeyboardButton(
            text="📨Техническая поддержка",
            url=f'{maintenance_link}'
        )
    ],
    [
        InlineKeyboardButton(
            text="⬅️Назад",
            callback_data='back_to_profile'
        )
    ]
]
maintenance_inline_keyboard = InlineKeyboardMarkup(inline_keyboard=maintenance_buttons,
                                                   resize_keyboard=True,
                                                   one_time_keyboard=True,
                                                   input_field_placeholder="Choice a button",
                                                   selective=True)

# Кнопки для выхода из раздела в профиль
checking_payment_buttons = [
    [
        InlineKeyboardButton(
            text="🧾Отправить квитанцию",
            url=f'{maintenance_link}'
        )
    ],
    [
        InlineKeyboardButton(
            text="⬅️Назад",
            callback_data='back_to_profile'
        )
    ]
]
checking_payment_inline_keyboard = InlineKeyboardMarkup(inline_keyboard=checking_payment_buttons,
                                                        resize_keyboard=True,
                                                        one_time_keyboard=True,
                                                        input_field_placeholder="Choice a button",
                                                        selective=True)

# Кнопки для способов пополнения баланса
way_to_increase_balance_buttons = [
    [
        InlineKeyboardButton(
            text="Пополнить через банк.карту",
            callback_data='way_to_increase_balance_bankcard'
        )
    ]
]
way_to_increase_balance_inline_keyboard = InlineKeyboardMarkup(inline_keyboard=way_to_increase_balance_buttons,
                                                               resize_keyboard=True,
                                                               one_time_keyboard=True,
                                                               input_field_placeholder="Choice a button",
                                                               selective=True)

# Кнопки для выхода из раздела в профиль
back_to_profile_buttons2 = [
    [
        InlineKeyboardButton(
            text="⬅️Назад",
            callback_data='back_to_profile2'
        )
    ]
]
back_to_profile_inline_keyboard2 = InlineKeyboardMarkup(inline_keyboard=back_to_profile_buttons2,
                                                       resize_keyboard=True,
                                                       one_time_keyboard=True,
                                                       input_field_placeholder="Choice a button",
                                                       selective=True)

# Кнопки для выхода из раздела в профиль
back_to_profile_buttons = [
    [
        InlineKeyboardButton(
            text="⬅️Назад",
            callback_data='back_to_profile'
        )
    ]
]
back_to_profile_inline_keyboard = InlineKeyboardMarkup(inline_keyboard=back_to_profile_buttons,
                                                       resize_keyboard=True,
                                                       one_time_keyboard=True,
                                                       input_field_placeholder="Choice a button",
                                                       selective=True)

# Кнопки для профиля
profile_buttons = [
    [
        InlineKeyboardButton(
            text="👤Профиль",
            callback_data='profile'
        ),
    ],
    [
        InlineKeyboardButton(
            text="💸Пополнить баланс",
            callback_data='deposit'
        )
    ],
    [
        InlineKeyboardButton(
            text="🐢Мои Creatures",
            callback_data='my_creature'
        ),
    ],
    [
        InlineKeyboardButton(
            text="🐲Creatures маркетплейс",
            callback_data='creature_market'
        ),
    ],
    [
        InlineKeyboardButton(
            text="📨Техническая поддержка",
            callback_data='maintenance'
        ),
    ],
    # [
    #     InlineKeyboardButton(
    #         text="⚙️Настройки",
    #         callback_data='settings'
    #     ),
    # ]
]
profile_inline_keyboard = InlineKeyboardMarkup(inline_keyboard=profile_buttons,
                                               resize_keyboard=True,
                                               one_time_keyboard=True,
                                               input_field_placeholder="Choice a button",
                                               selective=True)

# Кнопки для подтвержения соглашения
user_acceptation_buttons = [
    [
        InlineKeyboardButton(
            text="✅Принять",
            callback_data='user_acceptation'
        ),
    ]
]
user_acceptation_inline_keyboard = InlineKeyboardMarkup(inline_keyboard=user_acceptation_buttons,
                                                        resize_keyboard=True,
                                                        one_time_keyboard=True,
                                                        input_field_placeholder="Choice a button",
                                                        selective=True)

# Список эмоджи для капчи
emojis = ["🐶", "🐼", "🐵", "🐸", "🐷", "🐱"]

# Клавиатура с инлайн-кнопками для капчи (3 ряда по 2 кнопки)
capture_keyboard = types.InlineKeyboardMarkup(
    row_width=2,
    inline_keyboard=[
        [
            types.InlineKeyboardButton(text=emoji, callback_data=emoji)
            for emoji in emojis[:3]
        ],
        [
            types.InlineKeyboardButton(text=emoji, callback_data=emoji)
            for emoji in emojis[3:]
        ],
    ]
)
