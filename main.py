import asyncio
import logging
import sys


async def on_startup():
    from loader import dp, bot

    await dp.start_polling(bot)

if __name__ == "__main__":
    from handlers import dp

    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(on_startup())
