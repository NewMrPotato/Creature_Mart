# базы данных
import sqlite3

# aiogram
from aiogram.enums import ParseMode
from aiogram import types, F

# импорт внутри проекта
from handlers.users.start import delete_last_messages
from keyboards.inline.inline_buttons import profile_inline_keyboard, back_to_profile_inline_keyboard
from loader import router, dp, bot

# работа с изображениями
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO


# Выводим меню пользователю, если вызов из текстового сообщения
async def show_profile_text_request(message: types.Message):
    await message.answer('🌐<b>Меню</b>\n\n'
                         '<i>Выберите следующее действие:</i>', parse_mode=ParseMode.HTML, reply_markup=profile_inline_keyboard)


# Выводим меню пользователю, если вызов из callback
async def show_profile_callback_request(callback: types.CallbackQuery):
    await callback.message.answer('🌐<b>Меню</b>\n\n'
                                  '<i>Выберите следующее действие:</i>', parse_mode=ParseMode.HTML, reply_markup=profile_inline_keyboard)


@dp.message(F.text == "Меню🌐")
async def menu_demonstration(message: types.Message):
    # Подключаемся к базе данных
    conn = sqlite3.connect('data/database/database_shop.sqlite')
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users WHERE tg_id = ?", (message.from_user.id,))
    count = cursor.fetchone()[0]

    # Закрываем соединение с базой данных
    cursor.close()
    conn.close()

    if not (count > 0):  # проверка на существование пользователя в базе даннах
        await message.answer('У вас нет профиль в этом боте. Для создания профиля напишите /start')
    else:
        await show_profile_text_request(message)


# Добавление текста на изображение
def add_text_to_image(image_path, text, position, text_size, text_color):
    # Открываем изображение
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)

    # Загружаем шрифт и задаем размер текста
    font_path = "data/fonts/Arimo.ttf"  # Укажите путь к файлу шрифта
    font = ImageFont.truetype(font_path, text_size)

    # Добавляем текст на изображение
    draw.text(position, text, font=font, fill=text_color)

    return image


# Показываем профиль с информацией о пользователе
@router.callback_query(lambda query: query.data == "profile")
async def profile_handler(callback: types.CallbackQuery):
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

        # Подключение к базе данных
        conn = sqlite3.connect('data/database/database_shop.sqlite')
        cursor = conn.cursor()

        # Получаем данные по указанному идентификатору
        cursor.execute("SELECT * FROM users WHERE tg_id = ?", (callback.from_user.id,))
        result = cursor.fetchone()

        # Закрываем соединение с базой данных
        cursor.close()
        conn.close()

        # Определяем верифицирован ли пользователь
        if not (bool(result[3])):
            status = 'Не пройдена'
        else:
            status = 'Пройдена'

        caption = f'📂 Профиль: #{result[0]}\n' \
                  f'✅ Верификация: <b>{status}</b>\n' \
                  f'📅 Вы были зарегистрированы <b>{result[2]}</b>\n' \
                  f'➖➖➖➖➖➖➖➖➖➖\n' \
                  f'💵 Баланс: <b>{result[1]} ₽</b>'

        await callback.message.answer(caption, parse_mode=ParseMode.HTML,
                                      reply_markup=back_to_profile_inline_keyboard)
    else:
        await callback.message.answer('Вы были добавлены в черный список⚫️ \n\nДля вас доступ к боту запрещен!')

