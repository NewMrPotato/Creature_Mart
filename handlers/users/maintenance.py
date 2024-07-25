# aiogram
from aiogram.enums import ParseMode
from aiogram import types

# импорт внутри проекта
from handlers.users.different_functions import delete_last_messages
from handlers.users.start import user_acceptation_url
from keyboards.inline.inline_buttons import maintenance_inline_keyboard
from loader import router, dp, bot


# Выводит сообщения с инструкцией к обращению в поддержку
@router.callback_query(lambda query: query.data == "maintenance")
async def maintenance_handler(callback: types.CallbackQuery):
    await delete_last_messages(callback.message)

    caption = f'📨<b>Вы можете сообщить о проблеме или ошибке, обратившись в техническую поддержку.</b>\n\n' \
              f'Для того, чтобы наши специалисты могли помочь в сложившейся ситуации, вам необходимо:\n' \
              f'Либо ознакомиться с <a href="{user_acceptation_url}">пользовательским соглашением</a>\n\n' \
              f'-Представиться\n' \
              f'-Описать подробно проблему\n' \
              f'-Приложить соответствующие доказательства\n\n' \
              f'⚠️<i>Официальная техническая поддержка никогда не пишет первая пользователям, обязательно сверяйте контакты через бота.</i>'
    await callback.message.answer(caption, parse_mode=ParseMode.HTML, reply_markup=maintenance_inline_keyboard)
