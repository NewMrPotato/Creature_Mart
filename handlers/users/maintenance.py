from html import escape

from aiogram import F, types

from handlers.users.navigation import show_screen
from keyboards.inline.inline_buttons import maintenance_inline_keyboard
from loader import router, settings


@router.callback_query(F.data == "maintenance")
async def maintenance_handler(callback: types.CallbackQuery):
    caption = (
        "📨<b>Вы можете сообщить о проблеме или ошибке в техническую поддержку.</b>\n\n"
        f'Ознакомьтесь с <a href="{escape(settings.agreement_url, quote=True)}">пользовательским соглашением</a>.\n\n'
        "Представьтесь, подробно опишите проблему и приложите доказательства.\n\n"
        "⚠️Официальная поддержка никогда не пишет первой. Сверяйте контакты через бота."
    )
    await show_screen(callback, caption, reply_markup=maintenance_inline_keyboard)
