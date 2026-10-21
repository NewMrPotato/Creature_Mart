import asyncio

from aiogram import F, types

from handlers.users.profile import show_profile_callback_request
from loader import db, router


@router.callback_query(F.data == "user_acceptation")
async def accept_agreement(callback: types.CallbackQuery):
    created = await asyncio.to_thread(
        db.register, callback.from_user.id, callback.from_user.username
    )
    text = "Вы приняли соглашение! Ваш профиль создан👤" if created else "У вас уже есть профиль✅"
    await show_profile_callback_request(callback, notice=text)
