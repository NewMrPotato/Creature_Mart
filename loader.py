from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import SimpleEventIsolation

from config import load_settings
from database import Database

settings = load_settings()
db = Database(settings.database_path)
bot = Bot(token=settings.token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(events_isolation=SimpleEventIsolation())
router = Router()
dp.include_router(router)
