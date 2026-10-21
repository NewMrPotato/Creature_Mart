import asyncio

from aiogram import F, types

from handlers.users.profile import show_profile_callback_request
from loader import db, router


@router.callback_query(F.data.in_({"back_to_profile", "back_to_profile2"}))
async def back_to_profile(callback: types.CallbackQuery):
    await asyncio.to_thread(db.cancel, callback.from_user.id)
    await show_profile_callback_request(callback)
