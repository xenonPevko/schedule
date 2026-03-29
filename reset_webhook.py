import asyncio
from aiogram import Bot
from config import BOT_TOKEN

async def reset():
    bot = Bot(token=BOT_TOKEN)
    result = await bot.delete_webhook(drop_pending_updates=True)
    print(f"Webhook удалён: {result}")
    await bot.session.close()

if __name__ == "__main__":
    asyncio.run(reset())