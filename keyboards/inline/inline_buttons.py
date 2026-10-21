from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from loader import settings

COLLECTIONS = (
    "Celestial_Guardians",
    "Mystical_Beasts",
    "Legendary_Creatures",
    "Aquatic_Wonders",
    "Mythical_Figures",
    "Dreamweavers",
    "Cryptic_Oddities",
    "Elemental_Spirits",
)
emojis = ("🐶", "🐼", "🐵", "🐸", "🐷", "🐱")


def get_keyboard(items, prefix="market", back="creature_market"):
    buttons = [
        [
            InlineKeyboardButton(
                text=f"{item['collection'].replace('_', ' ')} #{item['number']} ({item['price']} RUB)",
                callback_data=f"{prefix}/{item['id']}",
            )
        ]
        for item in items
    ]
    buttons.append([InlineKeyboardButton(text="⬅️Назад", callback_data=back)])
    if back != "back_to_profile":
        buttons.append([InlineKeyboardButton(text="🏠В меню", callback_data="back_to_profile")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


back_to_profile_buttons = [[InlineKeyboardButton(text="🏠В меню", callback_data="back_to_profile")]]
back_to_profile_inline_keyboard = InlineKeyboardMarkup(inline_keyboard=back_to_profile_buttons)

start_market_buttons = [
    [
        InlineKeyboardButton(
            text=name.replace("_", " "), callback_data=name.lower() + "_collection"
        )
        for name in COLLECTIONS[index : index + 2]
    ]
    for index in range(0, len(COLLECTIONS), 2)
]
start_market_inline_keyboard = InlineKeyboardMarkup(
    inline_keyboard=start_market_buttons + back_to_profile_buttons
)

maintenance_inline_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📨Техническая поддержка", url=settings.support_url)],
        *back_to_profile_buttons,
    ]
)
checking_payment_inline_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🧾Отправить квитанцию", url=settings.support_url)],
        *back_to_profile_buttons,
    ]
)
way_to_increase_balance_inline_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Пополнить через банк.карту", callback_data="way_to_increase_balance_bankcard"
            )
        ],
        *back_to_profile_buttons,
    ]
)
profile_inline_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text=text, callback_data=callback)]
        for text, callback in (
            ("👤Профиль", "profile"),
            ("💸Пополнить баланс", "deposit"),
            ("🐢Мои Creatures", "my_creature"),
            ("🐲Creatures маркетплейс", "creature_market"),
            ("📨Техническая поддержка", "maintenance"),
        )
    ]
)
user_acceptation_inline_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="✅Принять", callback_data="user_acceptation")],
    ]
)
capture_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text=emoji, callback_data=emoji) for emoji in emojis[:3]],
        [InlineKeyboardButton(text=emoji, callback_data=emoji) for emoji in emojis[3:]],
    ]
)
