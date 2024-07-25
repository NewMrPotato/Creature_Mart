from aiogram import Bot, types, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

with open('data/text/config.txt', 'r') as f:
    lines = f.readlines()

token = lines[0].split('\\')[0].replace(' ', '')
bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

dp = Dispatcher()
router = Router()
dp.include_router(router)
